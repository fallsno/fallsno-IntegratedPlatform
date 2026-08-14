from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    FormulaTemplate,
    FormulaTemplateItem,
    FormulaTemplateModule,
    FormulaTemplateScene,
    ModelParameterValue,
    ModelVersion,
    ModelWorkbenchConfig,
    ParameterDefinition,
    WorkbenchFormula,
    WorkbenchFormulaModule,
    WorkbenchFormulaScene,
    ModelSelectionMapping,
    ModelFocusMetricConfig,
)
from app.services.workbench_calculator import calculate_workbench_instance
from app.services.formula_engine import evaluate_formula_expression

router = APIRouter(prefix="/workbench", tags=["workbench"])


def _resolve_template_for_product_type(db: Session, product_type_id: int):
    """按产品大类归并匹配公式模板。

    模板挂在 product_type 上，而同一产品大类（如“再生滚筒”）由多个
    product_type 归并而成。这里先按 product_type_id 精确匹配模板，
    匹配不到时，按“大类名”（normalize_drum_type_name）归并后，
    在同类其它 product_type 上查找活跃模板。
    """
    if not int(product_type_id or 0):
        return None
    exact = (
        db.query(FormulaTemplate)
        .filter(
            FormulaTemplate.product_type_id == int(product_type_id),
            FormulaTemplate.is_active == True,
        )
        .first()
    )
    if exact:
        return exact

    try:
        from app.services.drum_catalog import normalize_drum_type_name
        from app.models import ProductType

        current_pt = db.query(ProductType).filter(ProductType.id == int(product_type_id)).first()
        if not current_pt:
            return None
        category = normalize_drum_type_name(current_pt.type_name)
        if not category:
            return None
        sibling_pts = (
            db.query(ProductType.id)
            .filter(ProductType.id != int(product_type_id))
            .all()
        )
        for (sibling_id,) in sibling_pts:
            sibling_category = normalize_drum_type_name(
                db.query(ProductType.type_name).filter(ProductType.id == sibling_id).scalar() or ""
            )
            if sibling_category != category:
                continue
            template = (
                db.query(FormulaTemplate)
                .filter(
                    FormulaTemplate.product_type_id == sibling_id,
                    FormulaTemplate.is_active == True,
                )
                .first()
            )
            if template:
                return template
    except Exception:
        return None
    return None


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


def _build_template_structure(db: Session, template: FormulaTemplate) -> Dict[str, Any]:
    modules = (
        db.query(FormulaTemplateModule)
        .filter(FormulaTemplateModule.template_id == template.id)
        .order_by(FormulaTemplateModule.sort_order.asc(), FormulaTemplateModule.id.asc())
        .all()
    )

    template_data = {
        "template_id": template.id,
        "template_code": template.template_code,
        "template_name": template.template_name,
        "modules": [],
    }
    for mod in modules:
        mod_data = {
            "module_id": mod.id,
            "module_name": mod.module_name,
            "module_code": mod.module_code,
            "sort_order": mod.sort_order or 0,
            "scenes": [],
        }
        scenes = (
            db.query(FormulaTemplateScene)
            .filter(FormulaTemplateScene.module_id == mod.id)
            .order_by(FormulaTemplateScene.sort_order.asc(), FormulaTemplateScene.id.asc())
            .all()
        )
        for sc in scenes:
            sc_data = {
                "scene_id": sc.id,
                "scene_name": sc.scene_name,
                "scene_code": sc.scene_code,
                "scene_type": sc.scene_type,
                "sort_order": sc.sort_order or 0,
                "items": [],
            }
            items = (
                db.query(FormulaTemplateItem)
                .filter(FormulaTemplateItem.scene_id == sc.id)
                .order_by(FormulaTemplateItem.sort_order.asc(), FormulaTemplateItem.id.asc())
                .all()
            )
            for it in items:
                sc_data["items"].append(
                    {
                        "item_id": it.id,
                        "formula_name": it.formula_name,
                        "expression": it.expression,
                        "variables": _normalize_variables(it.variables),
                        "unit": it.unit or "",
                        "sort_order": it.sort_order or 0,
                        "description": it.description or "",
                        "resources": it.resources or [],
                        "output_flag": it.output_flag or "auto",
                    }
                )
            mod_data["scenes"].append(sc_data)
        template_data["modules"].append(mod_data)

    return template_data


def _build_model_params(
    db: Session,
    model_id: int,
    override_params: Dict[str, Any] | None = None,
) -> Dict[str, Dict[str, Any]]:
    params = (
        db.query(ModelParameterValue, ParameterDefinition)
        .join(ParameterDefinition, ModelParameterValue.parameter_id == ParameterDefinition.id)
        .filter(ModelParameterValue.version_id == model_id)
        .all()
    )

    model_params: Dict[str, Dict[str, Any]] = {}
    for p_val, p_def in params:
        model_params[p_def.param_name] = {
            "value": p_val.param_value,
            "unit": p_def.unit_code or "",
        }

    for name, value in (override_params or {}).items():
        param_name = str(name or "").strip()
        if not param_name:
            continue
        existing = model_params.get(param_name, {})
        model_params[param_name] = {
            "value": value,
            "unit": existing.get("unit", ""),
        }

    return model_params


def _build_latest_results(template_data: Dict[str, Any], computed_results: Dict[str, Dict[str, Any]]) -> list[Dict[str, Any]]:
    latest_results: list[Dict[str, Any]] = []
    for module in template_data.get("modules", []):
        for scene in module.get("scenes", []):
            for item in scene.get("items", []):
                formula_name = str(item.get("formula_name") or "").strip()
                if not formula_name:
                    continue
                result = computed_results.get(formula_name)
                if not result:
                    continue
                latest_results.append(
                    {
                        "scene_code": scene.get("scene_code") or "",
                        "scene_name": scene.get("scene_name") or "",
                        "result_code": formula_name,
                        "result_name": formula_name,
                        "result_value": str(result.get("value", "")),
                        "unit_code": result.get("unit", item.get("unit", "")),
                        "source_formula": formula_name,
                        "is_output": result.get("is_output", False),
                    }
                )
    return latest_results


def _execute_model_workbench(
    model_id: int,
    db: Session,
    override_params: Dict[str, Any] | None = None,
    module_code: str | None = None,
) -> Dict[str, Any]:
    config = db.query(ModelWorkbenchConfig).filter(ModelWorkbenchConfig.model_version_id == model_id).first()
    
    # 系统性筛查并自动纠正未挂载公式模板的问题
    if not config or not config.formula_template_id:
        version = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
        if version and version.family:
            family = version.family
            template_id = None
            
            # 1. 根据 family 的 default_template_code 查找
            if family.default_template_code:
                template = db.query(FormulaTemplate).filter(FormulaTemplate.template_code == family.default_template_code).first()
                if template:
                    template_id = template.id

            # 2. 根据 family 的 product_type_id 查找（含按产品大类归并匹配）
            if not template_id and family.product_type_id:
                template = _resolve_template_for_product_type(db, family.product_type_id)
                if template:
                    template_id = template.id

            # 3. 不再兜底“任意活跃模板”，避免把模板误挂到其它产品大类下的型号。
            if template_id:
                if not config:
                    config = ModelWorkbenchConfig(model_version_id=model_id, formula_template_id=template_id)
                    db.add(config)
                else:
                    config.formula_template_id = template_id
                db.commit()
                db.refresh(config)

    if not config or not config.formula_template_id:
        raise HTTPException(status_code=400, detail="该型号未挂载公式模板")
        
    template = db.query(FormulaTemplate).filter(FormulaTemplate.id == config.formula_template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="绑定的公式模板不存在")

    template_data = _build_template_structure(db, template)
    normalized_module_code = str(module_code or "").strip()
    if normalized_module_code:
        template_data["modules"] = [
            module
            for module in template_data.get("modules", [])
            if str(module.get("module_code") or "").strip() == normalized_module_code
        ]
        if not template_data["modules"]:
            raise HTTPException(status_code=404, detail="当前型号下不存在该计算模块")

    model_params = _build_model_params(db, model_id, override_params=override_params)
        
    try:
        results = calculate_workbench_instance(template_data, model_params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    scope = {
        name: detail.get("value")
        for name, detail in model_params.items()
    }
    scope.update({
        name: detail.get("value")
        for name, detail in results.items()
    })

    return {
        "status": "success",
        "data": {
            "template_id": template.id,
            "template_name": template.template_name,
            "template_structure": template_data,
            "computed_results": results,
            "latest_results": _build_latest_results(template_data, results),
            "scope": scope,
        },
    }


@router.get("/models/{model_id}/execute")
def execute_model_workbench(
    model_id: int,
    module_code: str | None = None,
    db: Session = Depends(get_db),
):
    return _execute_model_workbench(model_id, db, module_code=module_code)

@router.post("/models/{model_id}/formulas")
def save_template_formula(model_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    # Get the bound template
    config = db.query(ModelWorkbenchConfig).filter(ModelWorkbenchConfig.model_version_id == model_id).first()
    if not config or not config.formula_template_id:
        raise HTTPException(status_code=400, detail="该型号未挂载公式模板")
        
    template_id = config.formula_template_id
    
    module_code = str(payload.get("module_code") or "power_calc").strip()
    module_name = str(payload.get("module_name") or "功率计算").strip()
    scene_code = str(payload.get("scene_code") or "").strip()
    scene_name = str(payload.get("scene_name") or "未命名场景").strip()
    formula_name = str(payload.get("name") or "").strip()
    expression = str(payload.get("expression") or "").strip()
    
    if not scene_code or not formula_name:
        raise HTTPException(status_code=400, detail="scene_code 和 name 不能为空")
        
    # Ensure module exists
    module = db.query(FormulaTemplateModule).filter(
        FormulaTemplateModule.template_id == template_id,
        FormulaTemplateModule.module_code == module_code
    ).first()
    if not module:
        module = FormulaTemplateModule(
            template_id=template_id,
            module_code=module_code,
            module_name=module_name,
            sort_order=0
        )
        db.add(module)
        db.flush()
        
    # Ensure scene exists
    scene = db.query(FormulaTemplateScene).filter(
        FormulaTemplateScene.module_id == module.id,
        FormulaTemplateScene.scene_code == scene_code
    ).first()
    if not scene:
        scene = FormulaTemplateScene(
            module_id=module.id,
            scene_code=scene_code,
            scene_name=scene_name,
            sort_order=0
        )
        db.add(scene)
        db.flush()
        
    # Upsert item
    item = None
    item_id = payload.get("id")
    if item_id and int(item_id) > 0:
        item = db.query(FormulaTemplateItem).filter(FormulaTemplateItem.id == int(item_id)).first()
        
    if not item:
        item = db.query(FormulaTemplateItem).filter(
            FormulaTemplateItem.scene_id == scene.id,
            FormulaTemplateItem.formula_name == formula_name
        ).first()
        
    if not item:
        item = FormulaTemplateItem(scene_id=scene.id)
        db.add(item)
        
    item.formula_name = formula_name
    item.expression = expression
    item.variables = payload.get("variables") or {}
    if "description" in payload:
        item.description = payload.get("description")
    if "resources" in payload:
        item.resources = payload.get("resources") or []
    if "sort_order" in payload:
        item.sort_order = payload.get("sort_order") or 0
    
    db.commit()
    db.refresh(item)
    return {"status": "success", "id": item.id}

@router.delete("/models/{model_id}/formulas/{formula_id}")
def delete_template_formula(model_id: int, formula_id: int, db: Session = Depends(get_db)):
    config = db.query(ModelWorkbenchConfig).filter(ModelWorkbenchConfig.model_version_id == model_id).first()
    if not config or not config.formula_template_id:
        raise HTTPException(status_code=400, detail="该型号未挂载公式模板")
        
    item = db.query(FormulaTemplateItem).filter(FormulaTemplateItem.id == formula_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="公式不存在")
        
    db.delete(item)
    db.commit()
    return {"status": "success"}

@router.post("/models/{model_id}/formula-scenes")
def create_template_scene(model_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    config = db.query(ModelWorkbenchConfig).filter(ModelWorkbenchConfig.model_version_id == model_id).first()
    if not config or not config.formula_template_id:
        raise HTTPException(status_code=400, detail="该型号未挂载公式模板")
        
    template_id = config.formula_template_id
    module_code = payload.get("module_code")
    scene_name = payload.get("scene_name") or "未命名场景"
    
    if not module_code:
        raise HTTPException(status_code=400, detail="module_code 不能为空")
        
    module = db.query(FormulaTemplateModule).filter(
        FormulaTemplateModule.template_id == template_id,
        FormulaTemplateModule.module_code == module_code
    ).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
        
    import re
    base_code = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", scene_name).strip("_").lower() or "scene"
    
    existing_codes = {
        s.scene_code for s in db.query(FormulaTemplateScene).filter(FormulaTemplateScene.module_id == module.id).all()
    }
    
    scene_code = base_code
    suffix = 1
    while scene_code in existing_codes:
        scene_code = f"{base_code}_{suffix}"
        suffix += 1
        
    scene = FormulaTemplateScene(
        module_id=module.id,
        scene_code=scene_code,
        scene_name=scene_name,
        sort_order=len(existing_codes)
    )
    db.add(scene)
    db.commit()
    
    return {
        "module_code": module_code,
        "module_name": module.module_name,
        "scene_code": scene_code,
        "scene_name": scene_name
    }

@router.delete("/models/{model_id}/formula-modules/{module_code}/formula-scenes/{scene_code}")
def delete_template_scene(model_id: int, module_code: str, scene_code: str, db: Session = Depends(get_db)):
    config = db.query(ModelWorkbenchConfig).filter(ModelWorkbenchConfig.model_version_id == model_id).first()
    if not config or not config.formula_template_id:
        raise HTTPException(status_code=400, detail="该型号未挂载公式模板")
        
    module = db.query(FormulaTemplateModule).filter(
        FormulaTemplateModule.template_id == config.formula_template_id,
        FormulaTemplateModule.module_code == module_code
    ).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
        
    scene = db.query(FormulaTemplateScene).filter(
        FormulaTemplateScene.module_id == module.id,
        FormulaTemplateScene.scene_code == scene_code
    ).first()
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
        
    db.query(FormulaTemplateItem).filter(FormulaTemplateItem.scene_id == scene.id).delete()
    db.delete(scene)
    db.commit()
    return {"status": "success"}

@router.patch("/models/{model_id}/formula-modules/{module_code}/formula-scenes/{scene_code}")
def rename_template_scene(model_id: int, module_code: str, scene_code: str, payload: Dict[str, Any], db: Session = Depends(get_db)):
    config = db.query(ModelWorkbenchConfig).filter(ModelWorkbenchConfig.model_version_id == model_id).first()
    if not config or not config.formula_template_id:
        raise HTTPException(status_code=400, detail="该型号未挂载公式模板")
        
    module = db.query(FormulaTemplateModule).filter(
        FormulaTemplateModule.template_id == config.formula_template_id,
        FormulaTemplateModule.module_code == module_code
    ).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
        
    scene = db.query(FormulaTemplateScene).filter(
        FormulaTemplateScene.module_id == module.id,
        FormulaTemplateScene.scene_code == scene_code
    ).first()
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
        
    scene.scene_name = payload.get("scene_name") or scene.scene_name
    db.commit()
    return {"status": "success", "scene_name": scene.scene_name}


@router.post("/models/{model_id}/execute")
def execute_model_workbench_with_overrides(
    model_id: int,
    payload: Dict[str, Any] | None = None,
    module_code: str | None = None,
    db: Session = Depends(get_db),
):
    parameters = (payload or {}).get("parameters") or {}
    if not isinstance(parameters, dict):
        raise HTTPException(status_code=400, detail="parameters 必须是对象")
    return _execute_model_workbench(
        model_id,
        db,
        override_params=parameters,
        module_code=module_code,
    )

@router.post("/models/{model_id}/mount-template")
def mount_formula_template(
    model_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    template_id = payload.get("template_id")
    if not template_id:
        raise HTTPException(status_code=400, detail="template_id 不能为空")
        
    config = db.query(ModelWorkbenchConfig).filter(ModelWorkbenchConfig.model_version_id == model_id).first()
    if not config:
        config = ModelWorkbenchConfig(model_version_id=model_id, formula_template_id=template_id)
        db.add(config)
    else:
        config.formula_template_id = template_id
    db.commit()
    return {"status": "success", "message": "挂载成功"}

@router.post("/migrate-formulas-to-template/{source_version_id}")
def migrate_formulas_to_template_endpoint(
    source_version_id: int,
    db: Session = Depends(get_db)
):
    """
    专用迁移接口：将某个已完成公式计算的型号(例如HTS200)的公式提取为真实的通用公式模板，
    并自动为该系列下所有型号挂载此模板。
    """
    from app.models import (
        ModelFamily, WorkbenchFormula, WorkbenchFormulaModule, WorkbenchFormulaScene,
        FormulaTemplate, FormulaTemplateModule, FormulaTemplateScene, FormulaTemplateItem
    )
    
    version = db.query(ModelVersion).filter(ModelVersion.id == source_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail=f"找不到型号版本 ID: {source_version_id}")
        
    old_formulas = db.query(WorkbenchFormula).filter(WorkbenchFormula.version_id == source_version_id).order_by(WorkbenchFormula.sort_order).all()
    if not old_formulas:
        raise HTTPException(status_code=400, detail=f"型号版本 ID: {source_version_id} 没有任何历史公式，无法迁移为模板")
        
    family = db.query(ModelFamily).filter(ModelFamily.id == version.family_id).first() if version.family_id else None
    family_name = family.family_name if family else version.version_code
    template_code = f"TPL_{family_name}_GEN"
    template_name = f"{family_name} 通用计算模板"
    
    template = db.query(FormulaTemplate).filter(FormulaTemplate.template_code == template_code).first()
    if not template:
        template = FormulaTemplate(
            template_code=template_code,
            template_name=template_name,
            product_type_id=family.product_type_id if family else None,
            description=f"从 {version.display_name or version.version_code} 实例中提取的真实计算模板",
            is_active=True
        )
        db.add(template)
        db.commit()
        db.refresh(template)
    else:
        db.query(FormulaTemplateModule).filter(FormulaTemplateModule.template_id == template.id).delete()
        db.commit()

    old_modules = db.query(WorkbenchFormulaModule).filter(WorkbenchFormulaModule.version_id == source_version_id).all()
    old_scenes = db.query(WorkbenchFormulaScene).filter(WorkbenchFormulaScene.version_id == source_version_id).all()
    
    mod_map = {}
    for o_mod in old_modules:
        n_mod = FormulaTemplateModule(
            template_id=template.id,
            module_code=o_mod.module_code,
            module_name=o_mod.module_name,
            sort_order=o_mod.sort_order
        )
        db.add(n_mod)
        db.flush()
        mod_map[o_mod.module_code] = n_mod.id
        
    scene_map = {}
    for o_scene in old_scenes:
        n_scene = FormulaTemplateScene(
            module_id=mod_map.get(o_scene.module_code),
            scene_code=o_scene.scene_code,
            scene_name=o_scene.scene_name,
            sort_order=o_scene.sort_order
        )
        db.add(n_scene)
        db.flush()
        scene_map[o_scene.scene_code] = n_scene.id
        
    for o_form in old_formulas:
        mod_code = o_form.module_code or "default"
        scene_code = o_form.scene_code or "default"
        
        if mod_code not in mod_map:
            n_mod = FormulaTemplateModule(template_id=template.id, module_code=mod_code, module_name=o_form.module_name or "默认计算块")
            db.add(n_mod)
            db.flush()
            mod_map[mod_code] = n_mod.id
            
        if scene_code not in scene_map:
            n_scene = FormulaTemplateScene(module_id=mod_map[mod_code], scene_code=scene_code, scene_name=o_form.scene_name or "默认场景")
            db.add(n_scene)
            db.flush()
            scene_map[scene_code] = n_scene.id
            
        n_item = FormulaTemplateItem(
            scene_id=scene_map[scene_code],
            formula_name=o_form.name,
            expression=o_form.expression,
            variables=o_form.variables,
            unit="", 
            description=o_form.description,
            resources=o_form.resources,
            sort_order=o_form.sort_order
        )
        db.add(n_item)
        
    db.commit()
    
    # 为系列下所有型号挂载此新模板
    mounted_count = 0
    if version.family_id:
        siblings = db.query(ModelVersion).filter(ModelVersion.family_id == version.family_id).all()
        for sib in siblings:
            config = db.query(ModelWorkbenchConfig).filter(ModelWorkbenchConfig.model_version_id == sib.id).first()
            if not config:
                config = ModelWorkbenchConfig(model_version_id=sib.id, formula_template_id=template.id)
                db.add(config)
            else:
                config.formula_template_id = template.id
            mounted_count += 1
        
        if family:
            family.default_template_code = template.template_code
            
        db.commit()
        
    return {
        "status": "success", 
        "message": f"成功将 {len(old_formulas)} 条公式升格为模板 {template.template_name}，并已挂载到同系列 {mounted_count} 个型号上。"
    }

@router.get("/models/{model_id}/selection-mappings")
def get_selection_mappings(model_id: int, db: Session = Depends(get_db)):
    mappings = db.query(ModelSelectionMapping).filter(ModelSelectionMapping.version_id == model_id).all()
    return {
        "status": "success",
        "data": [
            {
                "id": m.id,
                "target_category": m.target_category,
                "target_field": m.target_field,
                "source_parameter": m.source_parameter,
            }
            for m in mappings
        ]
    }

@router.post("/models/{model_id}/selection-mappings")
def save_selection_mappings(model_id: int, payload: List[Dict[str, Any]], db: Session = Depends(get_db)):
    # Clear existing mappings for this model_id
    db.query(ModelSelectionMapping).filter(ModelSelectionMapping.version_id == model_id).delete()
    
    # Add new mappings
    for item in payload:
        mapping = ModelSelectionMapping(
            version_id=model_id,
            target_category=item.get("target_category"),
            target_field=item.get("target_field"),
            source_parameter=item.get("source_parameter")
        )
        db.add(mapping)
        
    db.commit()
    return {"status": "success", "message": "Selection mappings saved successfully."}


@router.get("/models/{model_id}/focus-metric-configs")
def get_focus_metric_configs(model_id: int, db: Session = Depends(get_db)):
    """读取某型号全部关注指标参考区间配置（按型号独立）。"""
    rows = (
        db.query(ModelFocusMetricConfig)
        .filter(ModelFocusMetricConfig.version_id == model_id)
        .all()
    )
    return {
        "status": "success",
        "data": [
            {
                "id": row.id,
                "metric_name": row.metric_name,
                "config": row.config or {},
            }
            for row in rows
        ],
    }


@router.put("/models/{model_id}/focus-metric-configs")
def save_focus_metric_configs(
    model_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """整体覆盖保存某型号的关注指标参考区间配置。

    payload 形如：{"configs": [{"metric_name": "产量", "config": {...}}]}
    仅影响当前型号，不影响同系列其它型号。
    """
    configs = payload.get("configs") or []
    existing = {
        row.metric_name: row
        for row in db.query(ModelFocusMetricConfig)
        .filter(ModelFocusMetricConfig.version_id == model_id)
        .all()
    }
    seen = set()
    for item in configs:
        metric_name = str(item.get("metric_name") or "").strip()
        if not metric_name:
            continue
        seen.add(metric_name)
        config = item.get("config") or {}
        row = existing.get(metric_name)
        if row:
            row.config = config
        else:
            db.add(ModelFocusMetricConfig(version_id=model_id, metric_name=metric_name, config=config))
    # 删除本次未提交的旧配置，保证整体覆盖语义
    for name, row in existing.items():
        if name not in seen:
            db.delete(row)
    db.commit()
    return {"status": "success", "message": "Focus metric configs saved successfully."}
