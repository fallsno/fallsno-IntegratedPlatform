from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from typing import List, Dict, Any
from app.database import get_db
from app.models import (
    ProductType, ProductComponent, ComponentParameter,
    ComponentDesignFlow, ComponentFlowStep, OperationHistory
)
from app.schemas import ProductTypeCreate, ProductTypeOut
import json

router = APIRouter(prefix="/product-types", tags=["product-types"])

def record_operation(db: Session, operation_type: str, module: str, entity_id: int, 
                     before_data: Dict[str, Any] = None, after_data: Dict[str, Any] = None,
                     context: Dict[str, Any] = None):
    history = OperationHistory(
        operation_type=operation_type,
        module=module,
        entity_id=entity_id,
        before_data=before_data,
        after_data=after_data,
        context=context
    )
    db.add(history)
    db.commit()

@router.get("/", response_model=List[ProductTypeOut])
def list_types(db: Session = Depends(get_db)):
    return db.query(ProductType).all()

@router.post("/", response_model=ProductTypeOut)
def create_type(data: ProductTypeCreate, db: Session = Depends(get_db)):
    db_type = ProductType(**data.dict())
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

@router.get("/{type_id}", response_model=ProductTypeOut)
def get_type(type_id: int, db: Session = Depends(get_db)):
    pt = db.query(ProductType).get(type_id)
    if not pt:
        raise HTTPException(404, detail="Product type not found")
    return pt

@router.put("/{type_id}", response_model=ProductTypeOut)
def update_type(type_id: int, data: ProductTypeCreate, db: Session = Depends(get_db)):
    pt = db.query(ProductType).get(type_id)
    if not pt:
        raise HTTPException(404)
    for k, v in data.dict().items():
        setattr(pt, k, v)
    db.commit()
    return pt

@router.delete("/{type_id}")
def delete_type(type_id: int, db: Session = Depends(get_db)):
    pt = db.query(ProductType).options(
        selectinload(ProductType.components).selectinload(ProductComponent.parameters),
        selectinload(ProductType.components).selectinload(ProductComponent.design_flows).selectinload(ComponentDesignFlow.steps),
        selectinload(ProductType.components).selectinload(ProductComponent.children)
    ).get(type_id)
    
    if pt:
        def serialize_comp(comp):
            return {
                'index': comp.index,
                'code': comp.code,
                'model_code': comp.model_code,
                'name': comp.name,
                'quantity': comp.quantity,
                'parameters': [{
                    'name': p.name,
                    'value': p.value,
                    'unit': p.unit,
                    'param_type': p.param_type,
                    'formula': p.formula
                } for p in comp.parameters],
                'design_flows': [{
                    'flow_name': f.flow_name,
                    'sort_order': f.sort_order,
                    'steps': [{
                        'step_name': s.step_name,
                        'sort_order': s.sort_order,
                        'calculation_content': s.calculation_content
                    } for s in f.steps]
                } for f in comp.design_flows],
                'children': [serialize_comp(child) for child in comp.children]
            }

        before_data = {
            'id': pt.id,
            'type_code': pt.type_code,
            'model_code': pt.model_code,
            'type_name': pt.type_name,
            'english_name': pt.english_name,
            'category': pt.category,
            'version': pt.version,
            'publisher': pt.publisher,
            'description': pt.description,
            'components_tree': [serialize_comp(c) for c in pt.components if c.parent_id is None]
        }
        record_operation(db, 'delete', 'product_types', pt.id, before_data=before_data)
        db.delete(pt)
        db.commit()
    return {"ok": True}

@router.post("/{type_id}/clone", response_model=ProductTypeOut)
def clone_product_type(type_id: int, db: Session = Depends(get_db)):
    source_type = db.query(ProductType).options(
        selectinload(ProductType.components).selectinload(ProductComponent.parameters),
        selectinload(ProductType.components).selectinload(ProductComponent.design_flows).selectinload(ComponentDesignFlow.steps)
    ).get(type_id)
    
    if not source_type:
        raise HTTPException(404, detail="Source product type not found")
    
    # 生成唯一的 type_code
    base_code = source_type.type_code
    if "_clone" in base_code:
        base_code = base_code.split("_clone")[0]
    
    import time
    timestamp = int(time.time())
    new_code = f"{base_code}_clone_{timestamp}"
    
    # 也可以采用递增数字的方式，但时间戳更简单且几乎保证唯一
    
    new_type = ProductType(
        type_code=new_code,
        model_code=source_type.model_code,
        type_name=source_type.type_name + " (副本)",
        english_name=source_type.english_name,
        category=source_type.category,
        version=source_type.version,
        publisher=source_type.publisher,
        machine_model=source_type.machine_model,
        description=source_type.description
    )
    db.add(new_type)
    db.flush()
    
    old_to_new_component_ids = {}
    
    def clone_component(source_comp, new_parent_id=None):
        new_comp = ProductComponent(
            product_type_id=new_type.id,
            parent_id=new_parent_id,
            index=source_comp.index,
            code=source_comp.code,
            model_code=source_comp.model_code,
            name=source_comp.name,
            quantity=source_comp.quantity
        )
        db.add(new_comp)
        db.flush()
        old_to_new_component_ids[source_comp.id] = new_comp.id
        
        for source_param in source_comp.parameters:
            new_param = ComponentParameter(
                component_id=new_comp.id,
                name=source_param.name,
                value=source_param.value,
                unit=source_param.unit,
                param_type=source_param.param_type,
                formula=source_param.formula
            )
            db.add(new_param)
        
        for source_flow in source_comp.design_flows:
            new_flow = ComponentDesignFlow(
                component_id=new_comp.id,
                flow_name=source_flow.flow_name,
                sort_order=source_flow.sort_order
            )
            db.add(new_flow)
            db.flush()
            
            for source_step in source_flow.steps:
                new_step = ComponentFlowStep(
                    flow_id=new_flow.id,
                    step_name=source_step.step_name,
                    sort_order=source_step.sort_order,
                    calculation_content=source_step.calculation_content
                )
                db.add(new_step)
        
        for child in source_comp.children:
            clone_component(child, new_comp.id)
    
    for root_comp in [c for c in source_type.components if c.parent_id is None]:
        clone_component(root_comp)
    
    db.commit()
    db.refresh(new_type)
    
    after_data = {
        'id': new_type.id,
        'type_code': new_type.type_code,
        'model_code': new_type.model_code,
        'type_name': new_type.type_name,
        'english_name': new_type.english_name,
        'category': new_type.category,
        'version': new_type.version,
        'publisher': new_type.publisher,
        'machine_model': new_type.machine_model,
        'description': new_type.description
    }
    record_operation(db, 'clone', 'product_types', new_type.id, after_data=after_data, context={'source_type_id': type_id})
    
    return new_type

@router.post("/{type_id}/derive", response_model=ProductTypeOut)
def derive_product_type(type_id: int, payload: dict, db: Session = Depends(get_db)):
    """机型推演：克隆整个产品并按照缩放系数修改参数"""
    scale_factor = float(payload.get('scale_factor', 1.0))
    target_code = payload.get('target_code', '')
    target_name = payload.get('target_name', '')
    
    # 1. 首先执行标准的克隆流程
    source_type = db.query(ProductType).options(
        selectinload(ProductType.components).selectinload(ProductComponent.parameters),
        selectinload(ProductType.components).selectinload(ProductComponent.design_flows).selectinload(ComponentDesignFlow.steps)
    ).get(type_id)
    
    if not source_type:
        raise HTTPException(404, detail="Source product type not found")
        
    import time
    timestamp = int(time.time())
    new_type = ProductType(
        type_code=f"{target_code}_{timestamp}",
        model_code=target_code,
        type_name=target_name,
        english_name=source_type.english_name,
        category=source_type.category,
        version="V1.0",
        publisher=source_type.publisher,
        machine_model=target_code,
        description=f"基于 {source_type.type_name} 推演生成，缩放系数: {scale_factor}"
    )
    db.add(new_type)
    db.flush()
    
    def clone_and_scale_component(source_comp, new_parent_id=None):
        new_comp = ProductComponent(
            product_type_id=new_type.id,
            parent_id=new_parent_id,
            index=source_comp.index,
            code=source_comp.code,
            model_code=source_comp.model_code,
            name=source_comp.name,
            quantity=source_comp.quantity
        )
        db.add(new_comp)
        db.flush()
        
        # 克隆参数并缩放数值
        for source_param in source_comp.parameters:
            val = source_param.value
            if val and val.replace('.', '', 1).isdigit():
                val = str(round(float(val) * scale_factor, 2))
                
            new_param = ComponentParameter(
                component_id=new_comp.id,
                name=source_param.name,
                value=val,
                unit=source_param.unit,
                param_type=source_param.param_type,
                formula=source_param.formula
            )
            db.add(new_param)
        
        # 克隆流程
        for source_flow in source_comp.design_flows:
            new_flow = ComponentDesignFlow(
                component_id=new_comp.id,
                flow_name=source_flow.flow_name,
                sort_order=source_flow.sort_order
            )
            db.add(new_flow)
            db.flush()
            
            for source_step in source_flow.steps:
                content = source_step.calculation_content or {}
                # 对流程中的输入值也进行缩放
                if 'rows' in content:
                    for row in content['rows']:
                        if row.get('value') and str(row.get('value')).replace('.', '', 1).isdigit():
                            row['value'] = str(round(float(row['value']) * scale_factor, 2))
                            
                new_step = ComponentFlowStep(
                    flow_id=new_flow.id,
                    step_name=source_step.step_name,
                    sort_order=source_step.sort_order,
                    calculation_content=content
                )
                db.add(new_step)
        
        for child in source_comp.children:
            clone_and_scale_component(child, new_comp.id)
            
    for root_comp in [c for c in source_type.components if c.parent_id is None]:
        clone_and_scale_component(root_comp)
        
    db.commit()
    db.refresh(new_type)
    return new_type

@router.post("/batch-import-components")
def batch_import_components(payload: Dict[str, Any], db: Session = Depends(get_db)):
    component_name = payload.get("componentName")
    table_data = payload.get("tableData")
    
    if not component_name or not table_data:
        raise HTTPException(400, detail="Missing component name or table data")
    
    lines = [line.strip() for line in table_data.strip().split('\n') if line.strip()]
    if len(lines) < 2:
        raise HTTPException(400, detail="Table must have at least a header and one data row")
    
    # 解析表头，寻找代号列索引
    header = lines[0].split('\t')
    if len(header) < 2:
        header = lines[0].split()
        
    import re
    code_col_idx = -1
    # 规则1: 查找字母+数字组合的列作为代号列
    for i, h in enumerate(header):
        # 检查表头或者第一行数据是否符合字母+数字特征
        first_row_cols = lines[1].split('\t') if '\t' in lines[1] else lines[1].split()
        if i < len(first_row_cols) and re.match(r'^[a-zA-Z]+\d+', first_row_cols[i].strip()):
            code_col_idx = i
            break
            
    if code_col_idx == -1:
        # 备选：查找包含"代号"或"型号"字样的列
        for i, h in enumerate(header):
            if "代号" in h or "型号" in h:
                code_col_idx = i
                break
    
    if code_col_idx == -1:
        raise HTTPException(400, detail="Could not identify code column (Letter+Number format)")

    param_names = [h for i, h in enumerate(header) if i != code_col_idx and i > 0] # 排除系列和代号后的参数名
    
    # 定义业务映射规则
    CATEGORY_MAPPING = {
        ('GT', 'AT'): '干燥滚筒',
        ('RT', 'GTRS'): '顺流式再生滚筒',
        ('HT', 'GTRQ'): '逆流式再生滚筒',
        ('CTD', 'GFT'): '双回程干燥冷却滚筒'
    }
    
    DRYING_DRUM_MODELS = {
        '120': '1500',
        '160': '2000',
        '240': '3000',
        '320': '4000',
        '400': '5000'
    }

    created_count = 0
    for line in lines[1:]:
        cols = line.split('\t') if '\t' in line else line.split()
        if len(cols) <= code_col_idx: continue
        
        raw_code = cols[code_col_idx].strip()
        # 处理 GT320/AT320 这种多代号
        model_codes = [c.strip() for c in raw_code.replace('/', ' ').split() if c.strip()]
        
        for m_code in model_codes:
            # 规则2 & 3: 识别名称和机型
            type_name = "未知分类"
            machine_model = ""
            
            # 提取字母和数字部分
            match = re.match(r'^([a-zA-Z]+)(\d+)', m_code)
            if match:
                prefix = match.group(1).upper()
                num_part = match.group(2)
                
                # 区分 GT 与 GTR (GTRS/GTRQ)
                # 如果以 GTR 开头，应归类为再生滚筒，不能误判为 GT 干燥滚筒
                if prefix.startswith('GTR'):
                    if prefix == 'GTRQ':
                        type_name = '逆流式再生滚筒'
                    else:
                        type_name = '顺流式再生滚筒' # GTRS 或 默认 GTR
                else:
                    # 确定其他分类名称
                    for prefixes, cat in CATEGORY_MAPPING.items():
                        if prefix in prefixes:
                            type_name = cat
                            break
                
                # 确定机型数字
                if type_name == '干燥滚筒':
                    machine_model = DRYING_DRUM_MODELS.get(num_part, num_part)
                else:
                    machine_model = num_part
            
            # 查找或创建产品类型
            pt = db.query(ProductType).filter(ProductType.model_code == m_code).first()
            if not pt:
                # 尝试前缀匹配保底
                pt = db.query(ProductType).filter(ProductType.model_code.like(f"{m_code}%")).first()
            
            if not pt:
                # 自动创建缺失的型号
                pt = ProductType(
                    type_name=type_name,
                    type_code=m_code,
                    model_code=m_code,
                    machine_model=machine_model,
                    category="机械设计",
                    version="V1.0",
                    publisher="系统导入"
                )
                db.add(pt)
                db.flush()

            if pt:
                # 规则4: 查重逻辑 - 只要该代号下已有同名部件，就跳过
                existing_comp = db.query(ProductComponent).filter(
                    ProductComponent.product_type_id == pt.id,
                    ProductComponent.name == component_name,
                    ProductComponent.parent_id == None
                ).first()
                
                if existing_comp:
                    continue

                # 计算序号
                from sqlalchemy import func
                max_index = db.query(func.max(ProductComponent.index)).filter(
                    ProductComponent.product_type_id == pt.id,
                    ProductComponent.parent_id == None
                ).scalar() or 0
                
                # 创建部件
                new_comp = ProductComponent(
                    product_type_id=pt.id,
                    name=component_name,
                    index=max_index + 1,
                    code="", 
                    model_code="",
                    quantity="1"
                )
                db.add(new_comp)
                db.flush()
                
                # 创建流程
                new_flow = ComponentDesignFlow(
                    component_id=new_comp.id,
                    flow_name="基础参数",
                    sort_order=0
                )
                db.add(new_flow)
                db.flush()
                
                # 填充参数
                rows = []
                # 寻找参数列的数据 (排除代号列和系列列)
                param_val_start_idx = 2 # 假设前两列是系列和代号
                if code_col_idx == 0: param_val_start_idx = 1
                
                current_param_vals = cols[param_val_start_idx:]
                for i, p_name in enumerate(param_names):
                    val = current_param_vals[i] if i < len(current_param_vals) else ""
                    rows.append({
                        "name": p_name,
                        "expression": val,
                        "value": val,
                        "unit": "",
                        "note": "Excel 智能导入"
                    })
                
                new_step = ComponentFlowStep(
                    flow_id=new_flow.id,
                    step_name="表格数据导入",
                    sort_order=0,
                    calculation_content={"rows": rows}
                )
                db.add(new_step)
                created_count += 1
    
    db.commit()
    return {"ok": True, "created_count": created_count}

@router.post("/undo-last")
def undo_last_product_type(db: Session = Depends(get_db)):
    last_history = db.query(OperationHistory)\
        .filter(OperationHistory.module == 'product_types')\
        .order_by(OperationHistory.created_at.desc())\
        .first()
    
    if not last_history:
        raise HTTPException(404, detail="No operation to undo")
    
    if last_history.operation_type == 'delete':
        before_data = last_history.before_data
        if before_data:
            new_type = ProductType(
                type_code=before_data['type_code'],
                model_code=before_data.get('model_code'),
                type_name=before_data['type_name'],
                english_name=before_data.get('english_name'),
                category=before_data.get('category'),
                version=before_data.get('version'),
                publisher=before_data.get('publisher'),
                description=before_data.get('description')
            )
            db.add(new_type)
            db.flush()

            def reconstruct_comp(comp_data, parent_id=None):
                new_comp = ProductComponent(
                    product_type_id=new_type.id,
                    parent_id=parent_id,
                    index=comp_data.get('index'),
                    code=comp_data.get('code'),
                    model_code=comp_data.get('model_code'),
                    name=comp_data.get('name'),
                    quantity=comp_data.get('quantity')
                )
                db.add(new_comp)
                db.flush()

                for p_data in comp_data.get('parameters', []):
                    db.add(ComponentParameter(
                        component_id=new_comp.id,
                        name=p_data['name'],
                        value=p_data['value'],
                        unit=p_data['unit'],
                        param_type=p_data['param_type'],
                        formula=p_data['formula']
                    ))
                
                for f_data in comp_data.get('design_flows', []):
                    new_flow = ComponentDesignFlow(
                        component_id=new_comp.id,
                        flow_name=f_data['flow_name'],
                        sort_order=f_data['sort_order']
                    )
                    db.add(new_flow)
                    db.flush()
                    for s_data in f_data.get('steps', []):
                        db.add(ComponentFlowStep(
                            flow_id=new_flow.id,
                            step_name=s_data['step_name'],
                            sort_order=s_data['sort_order'],
                            calculation_content=s_data['calculation_content']
                        ))
                
                for child_data in comp_data.get('children', []):
                    reconstruct_comp(child_data, new_comp.id)

            for root_comp_data in before_data.get('components_tree', []):
                reconstruct_comp(root_comp_data)

            db.delete(last_history)
            db.commit()
            return {"ok": True, "message": "Undo delete successful", "type_id": new_type.id}
    
    elif last_history.operation_type == 'clone':
        after_data = last_history.after_data
        if after_data and 'id' in after_data:
            type_id = after_data['id']
            pt = db.query(ProductType).get(type_id)
            if pt:
                db.delete(pt)
                db.commit()
            db.delete(last_history)
            db.commit()
            return {"ok": True, "message": "Undo clone successful"}
    
    raise HTTPException(400, detail="Cannot undo this operation type")