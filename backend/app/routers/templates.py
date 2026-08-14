from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ComponentTemplateSyncLink, TemplateDefinition
from app.routers.product_components import (
    load_component_with_flows,
    replace_component_flows,
    serialize_component_flows,
    upsert_template_link,
)
from app.schemas import (
    ComponentTemplateSyncLinkOut,
    TemplateDefinitionOut,
    TemplateExecuteSyncRequest,
)
from app.services.template_sync import build_sync_result, summarize_sync_result

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/tree")
def get_template_tree(db: Session = Depends(get_db)):
    """获取多级模板继承树 (System -> Series -> Model)"""
    templates = db.query(TemplateDefinition).order_by(TemplateDefinition.template_code.asc()).all()
    
    # 构建树形结构
    template_map = {t.id: {
        "id": t.id,
        "template_code": t.template_code,
        "template_name": t.template_name,
        "template_type": t.template_type,
        "scope_type": t.scope_type,
        "scope_id": t.scope_id,
        "source_template_id": t.source_template_id,
        "version_no": t.version_no,
        "status": t.status,
        "description": t.description,
        "children": []
    } for t in templates}
    
    tree = []
    for t in templates:
        node = template_map[t.id]
        if t.source_template_id and t.source_template_id in template_map:
            template_map[t.source_template_id]["children"].append(node)
        else:
            tree.append(node)
            
    return tree

@router.get("/", response_model=List[TemplateDefinitionOut])
def list_templates(db: Session = Depends(get_db)):
    return db.query(TemplateDefinition).order_by(TemplateDefinition.template_code.asc()).all()


@router.get("/links", response_model=List[ComponentTemplateSyncLinkOut])
def list_template_links(component_id: int, db: Session = Depends(get_db)):
    links = db.query(ComponentTemplateSyncLink).filter(
        (ComponentTemplateSyncLink.source_component_id == component_id)
        | (ComponentTemplateSyncLink.target_component_id == component_id)
    ).all()
    return links


@router.get("/diff-preview")
def preview_template_diff(
    source_component_id: int,
    target_component_id: int,
    db: Session = Depends(get_db),
):
    source_component = load_component_with_flows(db, source_component_id)
    target_component = load_component_with_flows(db, target_component_id)
    if not source_component or not target_component:
        raise HTTPException(status_code=404, detail="component not found")

    sync_result = build_sync_result(
        serialize_component_flows(source_component),
        serialize_component_flows(target_component),
        "overwrite_template_scope",
    )
    return summarize_sync_result(sync_result)


@router.post("/execute-sync")
def execute_template_sync(
    data: TemplateExecuteSyncRequest, db: Session = Depends(get_db)
):
    source_component = load_component_with_flows(db, data.source_component_id)
    target_component = load_component_with_flows(db, data.target_component_id)
    if not source_component or not target_component:
        raise HTTPException(status_code=404, detail="component not found")

    sync_result = build_sync_result(
        serialize_component_flows(source_component),
        serialize_component_flows(target_component),
        data.sync_mode or "overwrite_template_scope",
    )
    replace_component_flows(db, target_component, sync_result["flows"])
    link = upsert_template_link(
        db,
        source_component=source_component,
        target_component=target_component,
        sync_mode=data.sync_mode or "overwrite_template_scope",
        source_signature=sync_result["source_signature"],
    )
    db.commit()
    db.refresh(link)
    return {
        "link_id": link.id,
        "summary": summarize_sync_result(sync_result),
    }
