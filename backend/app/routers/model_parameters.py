from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FormulaTemplateModule, ModelFamily, ModelVersion
from app.schemas import (
    FamilyMatrixSaveRequest,
    ParameterDistributionOut,
    WorkbenchParameterSaveRequest,
    WorkbenchSnapshotCreateRequest,
)
from app.services.model_parameter_matrix import (
    MatrixValidationError,
    build_family_matrix,
    build_parameter_distribution,
    build_parameter_stats,
    delete_model_parameter_value,
    get_latest_workbench_snapshot,
    save_family_matrix_rows,
    save_workbench_parameter_rows,
    save_workbench_snapshot_rows,
)

router = APIRouter(prefix="/model-parameters", tags=["model-parameters"])


def _resolve_module_id(db: Session, module_code=None, module_id=None):
    """把 module_code 解析为模块记录 id（返回 (module_id, module_code) 或 (None, None)）。"""
    if module_id:
        return int(module_id), None
    code = str(module_code or "").strip()
    if not code:
        return None, None
    record = (
        db.query(FormulaTemplateModule)
        .filter(FormulaTemplateModule.module_code == code)
        .order_by(FormulaTemplateModule.id.asc())
        .first()
    )
    if not record:
        return None, None
    return record.id, code


@router.get("/workbench/snapshots/{version_id}/latest")
def get_latest_snapshot(version_id: int, db: Session = Depends(get_db)):
    return get_latest_workbench_snapshot(db, version_id)

@router.get("/families/{family_id}/matrix")
def get_family_matrix(
    family_id: int,
    module_code: str = "",
    module_id: int = None,
    db: Session = Depends(get_db),
):
    family = db.query(ModelFamily).filter(ModelFamily.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="family not found")
    versions = (
        db.query(ModelVersion)
        .filter(ModelVersion.family_id == family_id)
        .order_by(ModelVersion.created_at.asc(), ModelVersion.id.asc())
        .all()
    )
    resolved_module_id, _ = _resolve_module_id(db, module_code, module_id)
    return build_family_matrix(db, family, versions, module_id=resolved_module_id)


@router.put("/families/{family_id}/matrix")
def save_family_matrix(family_id: int, data: FamilyMatrixSaveRequest, db: Session = Depends(get_db)):
    family = db.query(ModelFamily).filter(ModelFamily.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="family not found")
    try:
        return save_family_matrix_rows(db, family_id, [row.model_dump() for row in data.rows])
    except MatrixValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/workbench/snapshots")
def create_workbench_snapshot(data: WorkbenchSnapshotCreateRequest, db: Session = Depends(get_db)):
    if not str(data.run_key or "").strip():
        raise HTTPException(status_code=400, detail="run_key 不能为空")
    try:
        return save_workbench_snapshot_rows(
            db,
            str(data.run_key).strip(),
            [row.model_dump() for row in data.rows],
        )
    except MatrixValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/workbench/parameters")
def save_workbench_parameters(data: WorkbenchParameterSaveRequest, db: Session = Depends(get_db)):
    family = db.query(ModelFamily).filter(ModelFamily.id == data.family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="family not found")
    resolved_module_id, _ = _resolve_module_id(db, data.module_code, data.module_id)
    try:
        return save_workbench_parameter_rows(
            db,
            data.family_id,
            [row.model_dump() for row in data.rows],
            module_id=resolved_module_id,
        )
    except MatrixValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/parameters/{parameter_id}/stats")
def get_parameter_stats(parameter_id: int, db: Session = Depends(get_db)):
    return build_parameter_stats(db, parameter_id)


@router.get("/parameters/{parameter_id}/distribution", response_model=ParameterDistributionOut)
def get_parameter_distribution(
    parameter_id: int,
    module_code: str = "",
    db: Session = Depends(get_db),
):
    try:
        resolved_module_id, _ = _resolve_module_id(db, module_code)
        return build_parameter_distribution(db, parameter_id, module_id=resolved_module_id)
    except MatrixValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/versions/{version_id}/parameters/{parameter_id}")
def delete_version_parameter_value(version_id: int, parameter_id: int, db: Session = Depends(get_db)):
    try:
        return delete_model_parameter_value(db, version_id, parameter_id)
    except MatrixValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
