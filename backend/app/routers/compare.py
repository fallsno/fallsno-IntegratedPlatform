from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FlowStep, PartDesignFlow, VersionPart, ModelVersion, ModelFamily, ComponentFlowStep, ProductComponent, ProductType

router = APIRouter(prefix="/compare", tags=["compare"])

@router.get("/design-point")
def compare_design_point(name: str, db: Session = Depends(get_db)):
    """对比不同型号下相同设计点的计算结果"""
    def safe_float(v):
        if v is None: return 0.0
        try:
            # 转换为字符串并彻底清洗
            s = str(v).strip().replace(',', '')
            # 处理可能的列表或 JSON 字符串形式
            if s.startswith('[') and s.endswith(']'):
                import json
                try:
                    vals = json.loads(s)
                    if isinstance(vals, list) and len(vals) > 0:
                        s = str(vals[0]).strip().replace(',', '')
                except:
                    pass
            
            # 提取第一个数字部分
            import re
            # 匹配整数、浮点数（包括负数）
            match = re.search(r'[-+]?\d*\.?\d+', s)
            if match:
                return float(match.group())
            return 0.0
        except:
            return 0.0

    try:
        design_point = name
        # 1. 搜索旧架构中的 FlowStep
        steps = db.query(FlowStep).filter(FlowStep.design_point == design_point).all()
        
        result = []
        for step in steps:
            flow = step.flow
            if not flow: continue
            part = flow.part
            if not part: continue
            version = part.version
            if not version: continue
            family = version.family
            if not family: continue
            
            outputs = [p for p in step.parameters if p.param_type == 'output']
            result.append({
                "type": "old",
                "family_code": family.family_code,
                "family_name": family.family_name,
                "version_code": version.version_code,
                "part_name": part.part_name,
                "flow_name": flow.flow_name,
                "step_name": f"步骤 {step.step_order}",
                "value": ", ".join([f"{p.param_name}={p.param_value}{p.param_unit}" for p in outputs]),
                "numeric_value": safe_float(outputs[0].param_value) if outputs else 0.0,
                "expression": "N/A (旧版架构)",
                "note": step.note
            })

        # 2. 搜索新架构中的 ComponentFlowStep (从 JSON 内容中搜索参数名)
        # 注意：这里我们搜索 calculation_content JSON 中的参数名
        all_steps = db.query(ComponentFlowStep).all()
        for c_step in all_steps:
            content = c_step.calculation_content or {}
            rows = content.get("rows", [])
            for row in rows:
                if row.get("name") == design_point:
                    flow = c_step.flow
                    comp = flow.component if flow else None
                    p_type = comp.product_type if comp else None
                    
                    val_raw = row.get('value')
                    expr_raw = row.get('expression', '')
                    
                    # 关键修复：如果当前值(value)为空，但计算式(expression)有值且不是公式（不以 = 开头），
                    # 则认为 expression 就是设计输入值，将其作为当前值处理
                    if not val_raw and expr_raw and not str(expr_raw).startswith('='):
                        val_raw = expr_raw
                    
                    numeric_val = safe_float(val_raw)
                    
                    # 如果仍为 0 且有单位，尝试从 unit 提取（处理部分导入数据偏移）
                    if numeric_val == 0 and row.get('unit'):
                        numeric_val = safe_float(row.get('unit'))

                    # 统一显示值格式
                    display_value = f"{val_raw or ''} {row.get('unit') or ''}".strip()

                    # 扩展逻辑：如果该组件所属的产品类型有关联的型号，则为每个型号生成一条记录
                    families = p_type.families if p_type else []
                    if families:
                        for fam in families:
                            result.append({
                                "type": "new",
                                "family_code": fam.family_code,
                                "family_name": fam.family_name,
                                "product_type_code": p_type.type_code if p_type else "N/A",
                                "product_type_model_code": p_type.model_code if p_type else "N/A",
                                "version_code": p_type.version if p_type else "N/A",
                                "machine_model": p_type.machine_model if p_type else None,
                                "part_name": comp.name if comp else "N/A",
                                "flow_name": flow.flow_name if flow else "N/A",
                                "step_name": c_step.step_name,
                                "value": display_value,
                                "numeric_value": numeric_val,
                                "expression": expr_raw,
                                "note": row.get('note')
                            })
                    else:
                        # 如果没有关联型号，则保留产品类型作为记录
                        result.append({
                            "type": "new",
                            "family_code": p_type.type_code if p_type else "N/A",
                            "family_name": p_type.type_name if p_type else "N/A",
                            "product_type_code": p_type.type_code if p_type else "N/A",
                            "product_type_model_code": p_type.model_code if p_type else "N/A",
                            "version_code": p_type.version if p_type else "N/A",
                            "machine_model": p_type.machine_model if p_type else None,
                            "part_name": comp.name if comp else "N/A",
                            "flow_name": flow.flow_name if flow else "N/A",
                            "step_name": c_step.step_name,
                            "value": display_value,
                            "numeric_value": numeric_val,
                            "expression": expr_raw,
                            "note": row.get('note')
                        })
        
        # 按照机型 (machine_model) 和产品代号进行排序
        def sort_key(item):
            # 将机型转为整数，如果没有则默认放到最后 (无穷大)
            try:
                m_model = int(item.get('machine_model')) if item.get('machine_model') else float('inf')
            except:
                m_model = float('inf')
            return (m_model, item.get('product_type_model_code', ''))
            
        result.sort(key=sort_key)
        
        return result
    except Exception as e:
        print(f"Error in compare_design_point: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
from typing import List, Optional

class CompareRequest(BaseModel):
    row_dimensions: List[str]  # e.g., ["product_type_model_code"]
    col_dimensions: List[str]  # e.g., ["part_name"]
    values: List[str]          # e.g., ["初始含水率W1 %", "产量"]

@router.post("/custom")
def custom_compare(req: CompareRequest, db: Session = Depends(get_db)):
    """多维透视对比接口"""
    def safe_float(v):
        if not v: return 0.0
        try:
            s = str(v).strip().replace(',', '')
            import re
            match = re.search(r'[-+]?\d*\.?\d+', s)
            if match: return float(match.group())
            return 0.0
        except: return 0.0

    # 提取所有相关的产品和参数
    all_steps = db.query(ComponentFlowStep).all()
    
    # 收集平铺的数据
    flat_data = []
    
    for c_step in all_steps:
        content = c_step.calculation_content or {}
        rows = content.get("rows", [])
        
        # 只关心请求的值
        matched_rows = [r for r in rows if r.get("name") in req.values]
        if not matched_rows: continue
            
        flow = c_step.flow
        comp = flow.component if flow else None
        p_type = comp.product_type if comp else None
        
        if not p_type: continue
        
        # 获取关联的型号名称
        families = p_type.families
        family_names = ", ".join([f.family_name for f in families]) if families else "N/A"
        family_codes = ", ".join([f.family_code for f in families]) if families else "N/A"
        
        base_record = {
            "product_type_code": p_type.type_code or "N/A",
            "product_type_model_code": p_type.model_code or "N/A",
            "type_name": p_type.type_name or "N/A",
            "machine_model": p_type.machine_model or "N/A",
            "family_name": family_names,
            "family_code": family_codes,
            "part_name": comp.name if comp else "N/A",
            "part_code": comp.code if comp else "N/A",
            "flow_name": flow.flow_name if flow else "N/A",
            "created_at": p_type.created_at.strftime("%Y-%m-%d") if p_type.created_at else "N/A",
        }
        
        for r in matched_rows:
            val_raw = r.get('value')
            expr_raw = r.get('expression', '')
            if not val_raw and expr_raw and not str(expr_raw).startswith('='):
                val_raw = expr_raw
            
            record = base_record.copy()
            record["param_name"] = r.get("name")
            record["value"] = safe_float(val_raw)
            record["raw_value"] = val_raw
            flat_data.append(record)

    # 在 Python 中构建透视表
    # 行键 -> { 列键 -> { param_name: value } }
    pivot_table = {}
    
    for d in flat_data:
        # 生成行键
        row_key = tuple(d.get(dim, "N/A") for dim in req.row_dimensions)
        row_key_str = " | ".join(str(k) for k in row_key)
        
        # 生成列键
        col_key = tuple(d.get(dim, "N/A") for dim in req.col_dimensions)
        col_key_str = " | ".join(str(k) for k in col_key)
        
        if row_key_str not in pivot_table:
            pivot_table[row_key_str] = {"_row_keys": dict(zip(req.row_dimensions, row_key))}
            
        if col_key_str not in pivot_table[row_key_str]:
            pivot_table[row_key_str][col_key_str] = {}
            
        pivot_table[row_key_str][col_key_str][d["param_name"]] = d["value"]
        
    return {
        "data": list(pivot_table.values()),
        "row_dims": req.row_dimensions,
        "col_dims": req.col_dimensions,
        "values": req.values
    }