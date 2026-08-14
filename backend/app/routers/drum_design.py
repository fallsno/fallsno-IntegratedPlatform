from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    DrumDesignAnalyzeOut,
    DrumDesignAnalyzeRequest,
    DrumDesignImpactAnalyzeOut,
    DrumDesignImpactAnalyzeRequest,
    DrumDesignCompareOut,
    DrumDesignCompareRequest,
    DrumDesignExecuteOut,
    DrumDesignExecuteRequest,
    DrumVerificationScanOut,
    DrumVerificationScanRequest,
    WorkbenchFormulaModuleCreateRequest,
    WorkbenchFormulaBatchDeleteOut,
    WorkbenchFormulaBatchDeleteRequest,
    WorkbenchFormulaDeleteOut,
    WorkbenchFormulaModuleDeleteOut,
    WorkbenchFormulaModuleListOut,
    WorkbenchFormulaModuleOut,
    WorkbenchTypeModuleEntryListOut,
    WorkbenchFormulaModuleRenameRequest,
    WorkbenchFormulaOut,
    WorkbenchFormulaReorderRequest,
    WorkbenchFormulaSceneCreateRequest,
    WorkbenchFormulaSceneDeleteOut,
    WorkbenchFormulaSceneOut,
    WorkbenchFormulaSceneRenameRequest,
    WorkbenchFormulaMappingSaveRequest,
    WorkbenchFormulaSyncPreviewOut,
    WorkbenchFormulaSyncPreviewRequest,
    WorkbenchFormulaSyncTargetsOut,
    WorkbenchFormulaSyncExecuteRequest,
    WorkbenchFormulaSyncExecuteOut,
    WorkbenchFormulaUpsertRequest,
)
from app.services.drum_design import (
    DrumDesignError,
    analyze_verification_scan,
    analyze_single_parameter,
    analyze_impact_for_result,
    build_case_compare_payload,
    create_formula_module,
    create_formula_scene,
    delete_formula_module,
    delete_model_formula,
    delete_model_formulas_batch,
    delete_formula_scene,
    execute_design_scenes,
    execute_formula_module_sync,
    list_type_module_entries,
    list_model_formula_modules,
    list_model_formulas,
    load_model_scene_formulas,
    preview_formula_module_sync,
    list_formula_sync_targets,
    list_formula_param_mappings,
    save_formula_param_mappings,
    rename_formula_module,
    rename_formula_scene,
    reorder_model_formulas,
    upsert_model_formula,
)


router = APIRouter(prefix="/drum-design", tags=["drum-design"])


@router.post("/execute", response_model=DrumDesignExecuteOut)
def execute_drum_design(payload: DrumDesignExecuteRequest, db: Session = Depends(get_db)):
    if not payload.model_id:
        raise HTTPException(status_code=400, detail="model_id 不能为空")
    try:
        return execute_design_scenes(
            payload.parameters,
            scene_formulas=load_model_scene_formulas(db, payload.model_id),
            db=db,
        )
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/analyze", response_model=DrumDesignAnalyzeOut)
def analyze_drum_design(payload: DrumDesignAnalyzeRequest, db: Session = Depends(get_db)):
    if not payload.model_id:
        raise HTTPException(status_code=400, detail="model_id 不能为空")
    try:
        return analyze_single_parameter(
            payload,
            scene_formulas=load_model_scene_formulas(db, payload.model_id),
        )
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/analyze-impact", response_model=DrumDesignImpactAnalyzeOut)
def analyze_drum_design_impact(payload: DrumDesignImpactAnalyzeRequest, db: Session = Depends(get_db)):
    if not payload.model_id:
        raise HTTPException(status_code=400, detail="model_id 不能为空")
    try:
        return analyze_impact_for_result(
            payload,
            scene_formulas=load_model_scene_formulas(db, payload.model_id),
        )
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/compare", response_model=DrumDesignCompareOut)
def compare_drum_design(payload: DrumDesignCompareRequest):
    try:
        return build_case_compare_payload(
            payload.mode,
            case_ids=payload.case_ids,
            family_id=payload.family_id,
            cases=payload.cases,
        )
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/product-types/{type_id}/module-entries", response_model=WorkbenchTypeModuleEntryListOut)
def get_type_module_entries(type_id: int, version_id: int | None = None, db: Session = Depends(get_db)):
    return list_type_module_entries(db, type_id, version_id)


@router.get("/models/{model_id}/formula-modules", response_model=WorkbenchFormulaModuleListOut)
def get_model_formula_modules(model_id: int, db: Session = Depends(get_db)):
    return list_model_formula_modules(db, model_id)


@router.post("/models/{model_id}/formula-modules", response_model=WorkbenchFormulaModuleOut)
def create_model_formula_module(
    model_id: int,
    payload: WorkbenchFormulaModuleCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        return create_formula_module(db, model_id, payload.module_name, getattr(payload, "module_code", "") or "")
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/models/{model_id}/formula-modules/{module_code}", response_model=WorkbenchFormulaModuleOut)
def rename_model_formula_module(
    model_id: int,
    module_code: str,
    payload: WorkbenchFormulaModuleRenameRequest,
    db: Session = Depends(get_db),
):
    try:
        return rename_formula_module(db, model_id, module_code, payload.module_name)
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/models/{model_id}/formula-sync-targets", response_model=WorkbenchFormulaSyncTargetsOut)
def get_formula_sync_targets(
    model_id: int,
    scope_type: str = "manual",
    version_ids: str = "",
    db: Session = Depends(get_db),
):
    parsed_ids = [int(item) for item in version_ids.split(",") if item.strip()]
    return list_formula_sync_targets(db, model_id, scope_type, parsed_ids)

@router.post(
    "/models/{model_id}/formula-modules/{module_code}/sync-preview",
    response_model=WorkbenchFormulaSyncPreviewOut,
)
def preview_model_formula_module_sync(
    model_id: int,
    module_code: str,
    payload: WorkbenchFormulaSyncPreviewRequest,
    db: Session = Depends(get_db),
):
    try:
        return preview_formula_module_sync(db, model_id, module_code, payload.scope_type, payload.target_version_ids)
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/models/{model_id}/formula-modules/{module_code}/sync", response_model=WorkbenchFormulaSyncExecuteOut)
def sync_formula_module_endpoint(
    model_id: int,
    module_code: str,
    payload: WorkbenchFormulaSyncExecuteRequest,
    db: Session = Depends(get_db),
):
    try:
        return execute_formula_module_sync(db, model_id, module_code, payload)
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

from typing import List
from app.schemas import WorkbenchFormulaMappingOut

@router.get("/models/{model_id}/formula-modules/{module_code}/param-mappings", response_model=List[WorkbenchFormulaMappingOut])
def get_formula_param_mappings(model_id: int, module_code: str, db: Session = Depends(get_db)):
    return list_formula_param_mappings(db, model_id, module_code)

@router.post("/models/{model_id}/formula-modules/{module_code}/param-mappings")
def save_formula_param_mappings_endpoint(model_id: int, module_code: str, payload: WorkbenchFormulaMappingSaveRequest, db: Session = Depends(get_db)):
    try:
        return save_formula_param_mappings(db, model_id, module_code, payload.mappings)
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post("/models/{model_id}/formula-scenes", response_model=WorkbenchFormulaSceneOut)
def create_model_formula_scene(
    model_id: int,
    payload: WorkbenchFormulaSceneCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        return create_formula_scene(db, model_id, payload.module_code, payload.scene_name)
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch(
    "/models/{model_id}/formula-modules/{module_code}/formula-scenes/{scene_code}",
    response_model=WorkbenchFormulaSceneOut,
)
def rename_model_formula_scene(
    model_id: int,
    module_code: str,
    scene_code: str,
    payload: WorkbenchFormulaSceneRenameRequest,
    db: Session = Depends(get_db),
):
    try:
        return rename_formula_scene(db, model_id, module_code, scene_code, payload.scene_name)
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/models/{model_id}/formula-modules/{module_code}", response_model=WorkbenchFormulaModuleDeleteOut)
def delete_model_formula_module(model_id: int, module_code: str, db: Session = Depends(get_db)):
    try:
        return delete_formula_module(db, model_id, module_code)
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete(
    "/models/{model_id}/formula-modules/{module_code}/formula-scenes/{scene_code}",
    response_model=WorkbenchFormulaSceneDeleteOut,
)
def delete_model_formula_scene(
    model_id: int,
    module_code: str,
    scene_code: str,
    db: Session = Depends(get_db),
):
    try:
        return delete_formula_scene(db, model_id, module_code, scene_code)
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/models/{model_id}/formulas", response_model=WorkbenchFormulaModuleListOut)
def get_model_formulas(model_id: int, db: Session = Depends(get_db)):
    return list_model_formulas(db, model_id)


@router.post("/models/{model_id}/formulas", response_model=WorkbenchFormulaOut)
def save_model_formula(
    model_id: int,
    payload: WorkbenchFormulaUpsertRequest,
    db: Session = Depends(get_db),
):
    if payload.model_id != model_id:
        raise HTTPException(status_code=400, detail="model_id 不匹配")
    try:
        return upsert_model_formula(db, payload)
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/models/{model_id}/formulas/batch-delete",
    response_model=WorkbenchFormulaBatchDeleteOut,
)
def delete_model_formulas_batch_endpoint(
    model_id: int,
    payload: WorkbenchFormulaBatchDeleteRequest,
    db: Session = Depends(get_db),
):
    try:
        return delete_model_formulas_batch(db, model_id, payload.formula_ids)
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete(
    "/models/{model_id}/formulas/{formula_id}",
    response_model=WorkbenchFormulaDeleteOut,
)
def delete_model_formula_endpoint(
    model_id: int,
    formula_id: int,
    db: Session = Depends(get_db),
):
    try:
        return delete_model_formula(db, model_id, formula_id)
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/models/{model_id}/formulas/reorder")
def reorder_formulas(
    model_id: int,
    payload: WorkbenchFormulaReorderRequest,
    db: Session = Depends(get_db),
):
    try:
        return reorder_model_formulas(db, model_id, payload.rows)
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/compare/verification-scan", response_model=DrumVerificationScanOut)
def compare_verification_scan(
    payload: DrumVerificationScanRequest,
    db: Session = Depends(get_db),
):
    try:
        return analyze_verification_scan(db, payload)
    except DrumDesignError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
