from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ParameterDefinition
from app.routers.product_components import (
    load_component_with_flows,
    serialize_component_parameter_rows,
)
from app.schemas import (
    ParameterDefinitionCreate,
    ParameterDefaultUpdateOut,
    ParameterDefaultUpdateRequest,
    ParameterDefinitionOut,
    ParameterLookupConfigOut,
    ParameterLookupConfigRequest,
    ParameterDefinitionUpdate,
    ParameterMatrixImportCommitOut,
    ParameterImportRequest,
    ParameterImportResult,
    ParameterMatrixImportCommitRequest,
    ParameterMatrixImportPreviewOut,
    ParameterMatrixImportPreviewRequest,
)
from app.services.parameter_catalog import (
    ParameterCatalogValidationError,
    normalize_parameter_payload,
)
from app.services.parameter_lookup_catalog import (
    ParameterLookupValidationError,
    get_parameter_lookup_config,
    save_parameter_lookup_config,
)
from app.services.model_parameter_matrix import (
    MatrixValidationError,
    build_parameter_center_matrix,
    build_parameter_stats,
    save_imported_parameter_matrix,
    delete_parameter_definition,
)
from app.services.parameter_matrix_import import build_parameter_matrix_preview

router = APIRouter(prefix="/parameters", tags=["parameters"])


@router.get("/", response_model=List[ParameterDefinitionOut])
def list_parameters(
    keyword: Optional[str] = None,
    category_code: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ParameterDefinition)
    if keyword:
        keyword = keyword.strip()
        if keyword:
            query = query.filter(
                (ParameterDefinition.param_code.ilike(f"%{keyword}%"))
                | (ParameterDefinition.param_name.ilike(f"%{keyword}%"))
                | (ParameterDefinition.display_name.ilike(f"%{keyword}%"))
            )
    if category_code:
        query = query.filter(ParameterDefinition.category_code == category_code)
    return query.order_by(ParameterDefinition.param_code.asc()).all()


@router.post("/", response_model=ParameterDefinitionOut)
def create_parameter(data: ParameterDefinitionCreate, db: Session = Depends(get_db)):
    try:
        payload = normalize_parameter_payload(data.model_dump())
    except ParameterCatalogValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    existing = (
        db.query(ParameterDefinition)
        .filter(ParameterDefinition.param_code == payload["param_code"])
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="param_code 已存在")

    row = ParameterDefinition(**payload)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{parameter_id}", response_model=ParameterDefinitionOut)
def update_parameter(
    parameter_id: int,
    data: ParameterDefinitionUpdate,
    db: Session = Depends(get_db),
):
    row = db.query(ParameterDefinition).filter(ParameterDefinition.id == parameter_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="parameter not found")

    try:
        payload = normalize_parameter_payload(data.model_dump())
    except ParameterCatalogValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    duplicated = (
        db.query(ParameterDefinition)
        .filter(ParameterDefinition.param_code == payload["param_code"])
        .filter(ParameterDefinition.id != parameter_id)
        .first()
    )
    if duplicated:
        raise HTTPException(status_code=400, detail="param_code 已存在")

    for key, value in payload.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.post("/import", response_model=ParameterImportResult)
def import_parameters(data: ParameterImportRequest, db: Session = Depends(get_db)):
    created_count = 0
    errors = []
    for index, row_data in enumerate(data.rows or [], start=1):
        try:
            payload = normalize_parameter_payload(row_data)
        except ParameterCatalogValidationError as exc:
            errors.append({"row_no": index, "message": str(exc)})
            continue

        existing = (
            db.query(ParameterDefinition)
            .filter(ParameterDefinition.param_code == payload["param_code"])
            .first()
        )
        if existing:
            errors.append({"row_no": index, "message": "param_code 已存在"})
            continue

        db.add(ParameterDefinition(**payload))
        created_count += 1

    db.commit()
    return {"created_count": created_count, "errors": errors}


@router.post("/matrix-import/preview", response_model=ParameterMatrixImportPreviewOut)
def preview_parameter_matrix_import(
    data: ParameterMatrixImportPreviewRequest,
    db: Session = Depends(get_db),
):
    return build_parameter_matrix_preview(
        db,
        data.rows,
        orientation_hint=data.orientation_hint,
    )


@router.post("/matrix-import/commit", response_model=ParameterMatrixImportCommitOut)
def commit_parameter_matrix_import(
    data: ParameterMatrixImportCommitRequest,
    db: Session = Depends(get_db),
):
    try:
        return save_imported_parameter_matrix(
            db,
            data.orientation,
            [row.model_dump() for row in data.parameter_rows],
        )
    except MatrixValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/matrix")
def get_parameter_center_matrix(
    keyword: Optional[str] = None,
    module_code: Optional[str] = "",
    module_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    resolved_module_id = None
    if module_id:
        resolved_module_id = int(module_id)
    elif module_code:
        from app.models import FormulaTemplateModule

        record = (
            db.query(FormulaTemplateModule)
            .filter(FormulaTemplateModule.module_code == str(module_code).strip())
            .order_by(FormulaTemplateModule.id.asc())
            .first()
        )
        if record:
            resolved_module_id = record.id
    return build_parameter_center_matrix(db, keyword=keyword, module_id=resolved_module_id)


@router.get("/references")
def list_parameter_references(comp_id: int, db: Session = Depends(get_db)):
    component = load_component_with_flows(db, comp_id)
    if not component:
        raise HTTPException(status_code=404, detail="component not found")
    return serialize_component_parameter_rows(component)


@router.get("/{parameter_id}/stats")
def get_parameter_stats(parameter_id: int, db: Session = Depends(get_db)):
    return build_parameter_stats(db, parameter_id)


@router.patch("/{parameter_id}/default", response_model=ParameterDefaultUpdateOut)
def update_parameter_default(
    parameter_id: int,
    data: ParameterDefaultUpdateRequest,
    db: Session = Depends(get_db),
):
    row = db.query(ParameterDefinition).filter(ParameterDefinition.id == parameter_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="parameter not found")
    row.default_value = data.default_value
    db.commit()
    db.refresh(row)
    payload = ParameterDefaultUpdateOut.model_validate(row)
    payload.sync_reason = data.reason
    return payload


@router.delete("/{parameter_id}")
def delete_parameter(parameter_id: int, db: Session = Depends(get_db)):
    try:
        return delete_parameter_definition(db, parameter_id)
    except MatrixValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{parameter_id}/lookup-config", response_model=ParameterLookupConfigOut)
def get_lookup_config(parameter_id: int, db: Session = Depends(get_db)):
    row = get_parameter_lookup_config(db, parameter_id)
    if not row:
        raise HTTPException(status_code=404, detail="lookup config not found")
    return row


@router.put("/{parameter_id}/lookup-config", response_model=ParameterLookupConfigOut)
def put_lookup_config(
    parameter_id: int,
    data: ParameterLookupConfigRequest,
    db: Session = Depends(get_db),
):
    try:
        return save_parameter_lookup_config(db, parameter_id, data.model_dump())
    except ParameterLookupValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
