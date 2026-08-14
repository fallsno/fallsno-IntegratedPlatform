from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FormulaTemplate, FormulaTemplateItem, FormulaTemplateModule, FormulaTemplateScene
from app.schemas import FormulaTemplateCreate, FormulaTemplateOut

router = APIRouter(prefix="/formula-templates", tags=["formula_templates"])


def _normalize_variables(variables: Any) -> Dict[str, str]:
    if isinstance(variables, dict):
        return {
            str(name).strip(): (value if isinstance(value, str) else "")
            for name, value in variables.items()
            if str(name).strip()
        }
    if isinstance(variables, list):
        return {
            str(name).strip(): ""
            for name in variables
            if str(name).strip()
        }
    return {}


def _serialize_template_structure(db: Session, template: FormulaTemplate) -> Dict[str, Any]:
    modules = (
        db.query(FormulaTemplateModule)
        .filter(FormulaTemplateModule.template_id == template.id)
        .order_by(FormulaTemplateModule.sort_order.asc(), FormulaTemplateModule.id.asc())
        .all()
    )

    return {
        "id": template.id,
        "template_code": template.template_code,
        "template_name": template.template_name,
        "product_type_id": template.product_type_id,
        "description": template.description,
        "is_active": template.is_active,
        "modules": [
            {
                "id": module.id,
                "module_code": module.module_code,
                "module_name": module.module_name,
                "sort_order": module.sort_order or 0,
                "scenes": [
                    {
                        "id": scene.id,
                        "scene_code": scene.scene_code,
                        "scene_name": scene.scene_name,
                        "sort_order": scene.sort_order or 0,
                        "items": [
                            {
                                "id": item.id,
                                "formula_name": item.formula_name,
                                "expression": item.expression,
                                "variables": _normalize_variables(item.variables),
                                "unit": item.unit or "",
                                "sort_order": item.sort_order or 0,
                            }
                            for item in (
                                db.query(FormulaTemplateItem)
                                .filter(FormulaTemplateItem.scene_id == scene.id)
                                .order_by(FormulaTemplateItem.sort_order.asc(), FormulaTemplateItem.id.asc())
                                .all()
                            )
                        ],
                    }
                    for scene in (
                        db.query(FormulaTemplateScene)
                        .filter(FormulaTemplateScene.module_id == module.id)
                        .order_by(FormulaTemplateScene.sort_order.asc(), FormulaTemplateScene.id.asc())
                        .all()
                    )
                ],
            }
            for module in modules
        ],
    }


def _replace_template_structure(db: Session, template: FormulaTemplate, payload: Dict[str, Any]) -> Dict[str, Any]:
    template.template_name = payload.get("template_name") or template.template_name
    template.template_code = payload.get("template_code") or template.template_code
    template.product_type_id = payload.get("product_type_id")
    template.description = payload.get("description")
    template.is_active = payload.get("is_active", True)

    old_modules = db.query(FormulaTemplateModule).filter(FormulaTemplateModule.template_id == template.id).all()
    for module in old_modules:
        old_scenes = db.query(FormulaTemplateScene).filter(FormulaTemplateScene.module_id == module.id).all()
        for scene in old_scenes:
            db.query(FormulaTemplateItem).filter(FormulaTemplateItem.scene_id == scene.id).delete()
        db.query(FormulaTemplateScene).filter(FormulaTemplateScene.module_id == module.id).delete()
    db.query(FormulaTemplateModule).filter(FormulaTemplateModule.template_id == template.id).delete()
    db.flush()

    modules = payload.get("modules") or []
    for module_index, module in enumerate(modules):
        module_row = FormulaTemplateModule(
            template_id=template.id,
            module_code=module.get("module_code") or f"module_{module_index + 1}",
            module_name=module.get("module_name") or f"模块 {module_index + 1}",
            sort_order=int(module.get("sort_order", module_index)),
        )
        db.add(module_row)
        db.flush()

        for scene_index, scene in enumerate(module.get("scenes") or []):
            scene_row = FormulaTemplateScene(
                module_id=module_row.id,
                scene_code=scene.get("scene_code") or f"scene_{scene_index + 1}",
                scene_name=scene.get("scene_name") or f"计算块 {scene_index + 1}",
                sort_order=int(scene.get("sort_order", scene_index)),
            )
            db.add(scene_row)
            db.flush()

            for item_index, item in enumerate(scene.get("items") or []):
                db.add(
                    FormulaTemplateItem(
                        scene_id=scene_row.id,
                        formula_name=item.get("formula_name") or f"公式 {item_index + 1}",
                        expression=item.get("expression") or "=0",
                        variables=_normalize_variables(item.get("variables")),
                        unit=item.get("unit") or "",
                        sort_order=int(item.get("sort_order", item_index)),
                    )
                )

    db.commit()
    db.refresh(template)
    return _serialize_template_structure(db, template)


@router.get("/", response_model=List[FormulaTemplateOut])
def list_templates(db: Session = Depends(get_db)):
    templates = db.query(FormulaTemplate).order_by(FormulaTemplate.template_code.asc(), FormulaTemplate.id.asc()).all()
    return templates

@router.post("/", response_model=FormulaTemplateOut)
def create_template(template: FormulaTemplateCreate, db: Session = Depends(get_db)):
    db_template = FormulaTemplate(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/{template_id}", response_model=FormulaTemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(FormulaTemplate).filter(FormulaTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.get("/{template_id}/structure")
def get_template_structure(template_id: int, db: Session = Depends(get_db)):
    template = db.query(FormulaTemplate).filter(FormulaTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return _serialize_template_structure(db, template)

@router.put("/{template_id}", response_model=FormulaTemplateOut)
def update_template(template_id: int, template_data: FormulaTemplateCreate, db: Session = Depends(get_db)):
    template = db.query(FormulaTemplate).filter(FormulaTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    for key, value in template_data.dict(exclude_unset=True).items():
        setattr(template, key, value)
    db.commit()
    db.refresh(template)
    return template


@router.put("/{template_id}/structure")
def update_template_structure(template_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    template = db.query(FormulaTemplate).filter(FormulaTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return _replace_template_structure(db, template, payload or {})

@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(FormulaTemplate).filter(FormulaTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
    return {"message": "Template deleted successfully"}
