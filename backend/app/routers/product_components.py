from copy import deepcopy
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
import os
import shutil
from app.database import get_db
from app.models import (
    ProductComponent,
    ComponentDesignFlow,
    ComponentFlowStep,
    ComponentParameter,
    ComponentTemplateSyncLink,
    OperationHistory,
)

def record_operation(db: Session, operation_type: str, module: str, entity_id: int, 
                     before_data: dict = None, after_data: dict = None, context: dict = None):
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
from app.schemas import (
    ProductComponentCreate, ProductComponentOut,
    ComponentDesignFlowCreate, ComponentDesignFlowOut,
    ComponentFlowStepBase, ComponentFlowStepCreate, ComponentFlowStepOut,
    ComponentTemplateSyncLinkOut, TemplateResyncRequest, TemplateSyncRequest, TemplateSyncResponse
)
from app.services.template_sync import (
    SYNC_MODE_OVERWRITE_TEMPLATE_SCOPE,
    build_sync_result,
    select_links_for_resync,
)

router = APIRouter(prefix="/product-components", tags=["product-components"])

def clone_component_recursive(db: Session, source_comp: ProductComponent, target_type_id: int, target_parent_id: Optional[int] = None):
    """递归克隆部件及其子部件、参数、设计流程和步骤"""
    new_comp = ProductComponent(
        product_type_id=target_type_id,
        parent_id=target_parent_id,
        index=source_comp.index,
        code=source_comp.code,
        model_code=source_comp.model_code,
        name=source_comp.name + " (副本)",
        quantity=source_comp.quantity
    )
    db.add(new_comp)
    db.flush()
    
    # 克隆参数
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
    
    # 克隆设计流程和步骤
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
    
    # 递归克隆子部件
    for child in source_comp.children:
        clone_component_recursive(db, child, target_type_id, new_comp.id)
    
    return new_comp


def load_component_with_flows(db: Session, component_id: int) -> Optional[ProductComponent]:
    return db.query(ProductComponent).options(
        selectinload(ProductComponent.design_flows).selectinload(ComponentDesignFlow.steps),
        selectinload(ProductComponent.template_source_links),
        selectinload(ProductComponent.template_target_links),
    ).get(component_id)


def serialize_component_flows(component: ProductComponent) -> List[dict]:
    flows_payload = []
    for flow in sorted(component.design_flows or [], key=lambda item: item.sort_order or 0):
        steps_payload = []
        for step in sorted(flow.steps or [], key=lambda item: item.sort_order or 0):
            steps_payload.append({
                "step_name": step.step_name,
                "sort_order": step.sort_order,
                "calculation_content": deepcopy(step.calculation_content or {"rows": []}),
            })

        flows_payload.append({
            "flow_name": flow.flow_name,
            "sort_order": flow.sort_order,
            "steps": steps_payload,
        })
    return flows_payload


def serialize_component_parameter_rows(component: ProductComponent) -> List[dict]:
    rows_payload = []
    for flow in sorted(component.design_flows or [], key=lambda item: item.sort_order or 0):
        for step in sorted(flow.steps or [], key=lambda item: item.sort_order or 0):
            for row in ((step.calculation_content or {}).get("rows") or []):
                rows_payload.append(
                    {
                        "component_id": component.id,
                        "flow_name": flow.flow_name,
                        "step_name": step.step_name,
                        "name": row.get("name"),
                        "unit": row.get("unit"),
                        "formula_id": row.get("formula_id"),
                        "formula_target": row.get("formula_target"),
                    }
                )
    return rows_payload


def replace_component_flows(db: Session, component: ProductComponent, flows_payload: List[dict]) -> None:
    for flow in list(component.design_flows or []):
        db.delete(flow)
    db.flush()

    for flow_payload in flows_payload or []:
        db_flow = ComponentDesignFlow(
            component_id=component.id,
            flow_name=flow_payload.get("flow_name"),
            sort_order=flow_payload.get("sort_order") or 0,
        )
        db.add(db_flow)
        db.flush()

        for step_payload in flow_payload.get("steps") or []:
            db.add(ComponentFlowStep(
                flow_id=db_flow.id,
                step_name=step_payload.get("step_name"),
                sort_order=step_payload.get("sort_order") or 0,
                calculation_content=deepcopy(step_payload.get("calculation_content") or {"rows": []}),
            ))


def upsert_template_link(
    db: Session,
    *,
    source_component: ProductComponent,
    target_component: ProductComponent,
    sync_mode: str,
    source_signature: str,
) -> ComponentTemplateSyncLink:
    link = db.query(ComponentTemplateSyncLink).filter(
        ComponentTemplateSyncLink.source_component_id == source_component.id,
        ComponentTemplateSyncLink.target_component_id == target_component.id,
    ).first()

    if not link:
        link = ComponentTemplateSyncLink(
            source_type_id=source_component.product_type_id,
            source_component_id=source_component.id,
            target_type_id=target_component.product_type_id,
            target_component_id=target_component.id,
        )
        db.add(link)

    link.sync_mode = sync_mode
    link.last_source_signature = source_signature
    return link

@router.post("/{comp_id}/clone")
def clone_component_api(
    comp_id: int, 
    target_type_id: int, 
    target_parent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    source_comp = db.query(ProductComponent).options(
        selectinload(ProductComponent.parameters),
        selectinload(ProductComponent.design_flows).selectinload(ComponentDesignFlow.steps),
        selectinload(ProductComponent.children)
    ).get(comp_id)
    
    if not source_comp:
        raise HTTPException(404, detail="Source component not found")
    
    new_comp = clone_component_recursive(db, source_comp, target_type_id, target_parent_id)
    db.commit()
    db.refresh(new_comp)
    return {"ok": True, "new_id": new_comp.id}

def build_component_tree(components: List[ProductComponent], parent_id: Optional[int] = None) -> List[ProductComponent]:
    tree = []
    for comp in components:
        if comp.parent_id == parent_id:
            comp.children = build_component_tree(components, comp.id)
            tree.append(comp)
    return sorted(tree, key=lambda x: x.index or 0)

@router.get("/{comp_id}", response_model=ProductComponentOut)
def get_component(comp_id: int, db: Session = Depends(get_db)):
    comp = db.query(ProductComponent).options(
        selectinload(ProductComponent.product_type)
    ).get(comp_id)
    if not comp:
        raise HTTPException(404, detail="Component not found")
    return comp

@router.get("/", response_model=List[ProductComponentOut])
def list_components(
    type_id: Optional[int] = None, 
    db: Session = Depends(get_db)
):
    q = db.query(ProductComponent).options(
        selectinload(ProductComponent.product_type)
    )
    if type_id:
        q = q.filter(ProductComponent.product_type_id == type_id)
    all_components = q.order_by(ProductComponent.index).all()
    
    # 构建完整的树形结构
    tree = build_component_tree(all_components, None)
    return tree

@router.post("/", response_model=ProductComponentOut)
def create_component(data: ProductComponentCreate, db: Session = Depends(get_db)):
    db_comp = ProductComponent(**data.dict())
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)
    return db_comp

@router.put("/{comp_id}", response_model=ProductComponentOut)
def update_component(comp_id: int, data: ProductComponentCreate, db: Session = Depends(get_db)):
    db_comp = db.query(ProductComponent).get(comp_id)
    if not db_comp:
        raise HTTPException(404)
    for k, v in data.dict().items():
        setattr(db_comp, k, v)
    db.commit()
    db.refresh(db_comp)
    return db_comp

@router.delete("/{comp_id}")
def delete_component(comp_id: int, db: Session = Depends(get_db)):
    db_comp = db.query(ProductComponent).get(comp_id)
    if db_comp:
        db.delete(db_comp)
        db.commit()
    return {"ok": True}

@router.post("/{comp_id}/reorder")
def single_reorder_component(comp_id: int, data: dict, db: Session = Depends(get_db)):
    db_comp = db.query(ProductComponent).get(comp_id)
    if not db_comp:
        raise HTTPException(404)
        
    new_parent_id = data.get('new_parent_id')
    new_index = data.get('new_index', 0)
    
    # 循环引用检测：检查 new_parent_id 是否是 comp_id 的子孙节点
    def check_circular(current_parent_id):
        if current_parent_id is None:
            return False
        if current_parent_id == comp_id:
            return True
        parent = db.query(ProductComponent).get(current_parent_id)
        if parent:
            return check_circular(parent.parent_id)
        return False
        
    if check_circular(new_parent_id):
        raise HTTPException(400, detail="循环引用：不能将节点移动到其子孙节点内部")
        
    before_data = {"parent_id": db_comp.parent_id, "index": db_comp.index}
        
    db_comp.parent_id = new_parent_id
    db_comp.index = new_index
    
    # 获取新的同级节点，重新排序其他节点
    siblings = db.query(ProductComponent).filter(
        ProductComponent.product_type_id == db_comp.product_type_id,
        ProductComponent.parent_id == new_parent_id,
        ProductComponent.id != comp_id
    ).order_by(ProductComponent.index).all()
    
    # 插入到新位置
    siblings.insert(new_index, db_comp)
    for i, sibling in enumerate(siblings):
        sibling.index = i
        
    db.commit()
    
    after_data = {"parent_id": new_parent_id, "index": new_index}
    record_operation(db, "reorder", "product_components", comp_id, before_data=before_data, after_data=after_data)
    
    return {"ok": True}

@router.post("/reorder")
def reorder_components(data: List[dict], db: Session = Depends(get_db)):
    for item in data:
        comp_id = item.get("id")
        db_comp = db.query(ProductComponent).get(comp_id)
        if db_comp:
            db_comp.index = item.get("index")
            db_comp.parent_id = item.get("parent_id")
    db.commit()
    return {"ok": True}

@router.get("/all-params-by-type/{type_id}")
def get_all_params_by_type(type_id: int, db: Session = Depends(get_db)):
    """获取指定产品类型下所有部件的所有设计参数"""
    components = db.query(ProductComponent).filter(
        ProductComponent.product_type_id == type_id
    ).options(
        selectinload(ProductComponent.design_flows).selectinload(ComponentDesignFlow.steps)
    ).all()
    
    all_params = []
    for comp in components:
        for flow in comp.design_flows:
            for step in flow.steps:
                content = step.calculation_content
                if content and 'rows' in content:
                    for row in content['rows']:
                        if row.get('name'):
                            all_params.append({
                                'name': row['name'],
                                'flow_name': flow.flow_name,
                                'component_name': comp.name,
                                'step_name': step.step_name,
                                'value': row.get('value'),
                                'unit': row.get('unit'),
                                'note': row.get('note')
                            })
    return all_params


@router.get("/{comp_id}/template-links", response_model=List[ComponentTemplateSyncLinkOut])
def get_template_links(comp_id: int, db: Session = Depends(get_db)):
    links = db.query(ComponentTemplateSyncLink).filter(
        (ComponentTemplateSyncLink.source_component_id == comp_id)
        | (ComponentTemplateSyncLink.target_component_id == comp_id)
    ).all()
    return links


@router.post("/{comp_id}/sync-template", response_model=TemplateSyncResponse)
def sync_component_template(comp_id: int, data: TemplateSyncRequest, db: Session = Depends(get_db)):
    source_component = load_component_with_flows(db, comp_id)
    if not source_component:
        raise HTTPException(404, detail="Source component not found")

    source_flows = serialize_component_flows(source_component)
    if not source_flows:
        raise HTTPException(400, detail="无可同步内容")

    results = []
    latest_signature = ""

    for target in data.targets:
        target_component = load_component_with_flows(db, target.target_component_id)
        if not target_component:
            raise HTTPException(
                404,
                detail=f"目标部件不存在: {target.target_component_id}",
            )
        if target_component.product_type_id != target.target_type_id:
            raise HTTPException(
                400,
                detail=f"目标部件 {target.target_component_id} 不属于型号 {target.target_type_id}",
            )

        sync_result = build_sync_result(
            source_flows,
            serialize_component_flows(target_component),
            data.sync_mode,
        )
        latest_signature = sync_result["source_signature"]
        replace_component_flows(db, target_component, sync_result["flows"])

        link = None
        if data.create_link:
            link = upsert_template_link(
                db,
                source_component=source_component,
                target_component=target_component,
                sync_mode=data.sync_mode,
                source_signature=sync_result["source_signature"],
            )
            db.flush()

        results.append({
            "target_type_id": target.target_type_id,
            "target_component_id": target.target_component_id,
            "sync_mode": data.sync_mode,
            "stats": sync_result["stats"],
            "link_id": getattr(link, "id", None),
        })

    db.commit()
    return {
        "source_component_id": source_component.id,
        "source_signature": latest_signature,
        "results": results,
    }


@router.post("/{comp_id}/resync-template", response_model=TemplateSyncResponse)
def resync_component_template(comp_id: int, data: TemplateResyncRequest, db: Session = Depends(get_db)):
    source_component = load_component_with_flows(db, comp_id)
    if not source_component:
        raise HTTPException(404, detail="Source component not found")

    source_flows = serialize_component_flows(source_component)
    if not source_flows:
        raise HTTPException(400, detail="无可同步内容")

    links = select_links_for_resync(
        source_component.id,
        [
            {
                "id": link.id,
                "source_component_id": link.source_component_id,
                "target_component_id": link.target_component_id,
                "target_type_id": link.target_type_id,
                "sync_mode": link.sync_mode,
            }
            for link in source_component.template_source_links or []
        ],
        target_component_ids=data.target_component_ids,
    )

    if not links:
        raise HTTPException(404, detail="未找到可重同步的模板关系")

    results = []
    latest_signature = ""

    for link_data in links:
        link = db.query(ComponentTemplateSyncLink).get(link_data["id"])
        target_component = load_component_with_flows(db, link.target_component_id)
        if not target_component:
            raise HTTPException(
                404,
                detail=f"目标部件不存在: {link.target_component_id}",
            )

        sync_mode = data.sync_mode or link.sync_mode or SYNC_MODE_OVERWRITE_TEMPLATE_SCOPE
        sync_result = build_sync_result(
            source_flows,
            serialize_component_flows(target_component),
            sync_mode,
        )
        latest_signature = sync_result["source_signature"]
        replace_component_flows(db, target_component, sync_result["flows"])
        link.sync_mode = sync_mode
        link.last_source_signature = sync_result["source_signature"]

        results.append({
            "target_type_id": target_component.product_type_id,
            "target_component_id": target_component.id,
            "sync_mode": sync_mode,
            "stats": sync_result["stats"],
            "link_id": link.id,
        })

    db.commit()
    return {
        "source_component_id": source_component.id,
        "source_signature": latest_signature,
        "results": results,
    }

# ---------- 设计流程 API ----------

@router.get("/{comp_id}/flows", response_model=List[ComponentDesignFlowOut])
def list_flows(comp_id: int, db: Session = Depends(get_db)):
    return db.query(ComponentDesignFlow).filter(ComponentDesignFlow.component_id == comp_id).all()

@router.post("/flows", response_model=ComponentDesignFlowOut)
def create_flow(data: ComponentDesignFlowCreate, db: Session = Depends(get_db)):
    db_flow = ComponentDesignFlow(**data.dict())
    db.add(db_flow)
    db.commit()
    db.refresh(db_flow)
    return db_flow

@router.put("/flows/{flow_id}", response_model=ComponentDesignFlowOut)
def update_flow(flow_id: int, data: ComponentDesignFlowCreate, db: Session = Depends(get_db)):
    db_flow = db.query(ComponentDesignFlow).get(flow_id)
    if not db_flow:
        raise HTTPException(404)
    for k, v in data.dict().items():
        setattr(db_flow, k, v)
    db.commit()
    db.refresh(db_flow)
    return db_flow

@router.post("/steps", response_model=ComponentFlowStepOut)
def create_step(data: ComponentFlowStepCreate, db: Session = Depends(get_db)):
    db_step = ComponentFlowStep(**data.dict())
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step

@router.put("/steps/{step_id}", response_model=ComponentFlowStepOut)
def update_step(step_id: int, data: ComponentFlowStepBase, db: Session = Depends(get_db)):
    db_step = db.query(ComponentFlowStep).get(step_id)
    if not db_step:
        raise HTTPException(404)
    for k, v in data.dict().items():
        setattr(db_step, k, v)
    db.commit()
    db.refresh(db_step)
    return db_step

@router.delete("/flows/{flow_id}")
def delete_flow(flow_id: int, db: Session = Depends(get_db)):
    db_flow = db.query(ComponentDesignFlow).get(flow_id)
    if db_flow:
        db.delete(db_flow)
        db.commit()
    return {"ok": True}

@router.delete("/steps/{step_id}")
def delete_step(step_id: int, db: Session = Depends(get_db)):
    db_step = db.query(ComponentFlowStep).get(step_id)
    if db_step:
        db.delete(db_step)
        db.commit()
    return {"ok": True}

# ---------- 参考资料文件上传 ----------

UPLOAD_DIR = "static/uploads/refs"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-ref")
async def upload_ref_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # 返回相对路径，前端通过 static 访问
    return {"file_path": f"/static/uploads/refs/{file.filename}"}
