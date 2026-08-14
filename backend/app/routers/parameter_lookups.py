from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ParameterLookupDefinitionCreate,
    ParameterLookupDefinitionOut,
    ParameterLookupCurvePreviewOut,
    ParameterLookupCurveProfilePayload,
    ParameterLookupImportPreviewOut,
    ParameterLookupImportPreviewRequest,
    ParameterLookupRowPayload,
    ParameterLookupRowsSaveOut,
    ParameterLookupRowsSaveRequest,
)
from app.services.parameter_lookup_catalog import (
    build_parameter_lookup_curve_preview,
    ParameterLookupValidationError,
    create_parameter_lookup,
    delete_parameter_lookup,
    get_parameter_lookup_curve_profile,
    list_parameter_lookup_rows,
    list_parameter_lookups,
    save_parameter_lookup_curve_profile,
    save_parameter_lookup_rows,
    update_parameter_lookup,
)
from app.services.parameter_lookup_import import build_parameter_lookup_import_preview

router = APIRouter(prefix="/parameter-lookups", tags=["parameter-lookups"])


@router.get("", response_model=List[ParameterLookupDefinitionOut])
def get_parameter_lookups(db: Session = Depends(get_db)):
    return list_parameter_lookups(db)


@router.post("", response_model=ParameterLookupDefinitionOut)
def post_parameter_lookup(data: ParameterLookupDefinitionCreate, db: Session = Depends(get_db)):
    try:
        return create_parameter_lookup(db, data.model_dump())
    except ParameterLookupValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{lookup_id}", response_model=ParameterLookupDefinitionOut)
def put_parameter_lookup(
    lookup_id: int,
    data: ParameterLookupDefinitionCreate,
    db: Session = Depends(get_db),
):
    try:
        return update_parameter_lookup(db, lookup_id, data.model_dump())
    except ParameterLookupValidationError as exc:
        detail = str(exc)
        status_code = 404 if detail == "lookup not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.delete("/{lookup_id}")
def remove_parameter_lookup(lookup_id: int, db: Session = Depends(get_db)):
    try:
        return delete_parameter_lookup(db, lookup_id)
    except ParameterLookupValidationError as exc:
        detail = str(exc)
        status_code = 404 if detail == "lookup not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.get("/{lookup_id}/rows", response_model=List[ParameterLookupRowPayload])
def get_parameter_lookup_rows(lookup_id: int, db: Session = Depends(get_db)):
    return list_parameter_lookup_rows(db, lookup_id)


@router.put("/{lookup_id}/rows", response_model=ParameterLookupRowsSaveOut)
def put_parameter_lookup_rows(
    lookup_id: int,
    data: ParameterLookupRowsSaveRequest,
    db: Session = Depends(get_db),
):
    try:
        return save_parameter_lookup_rows(db, lookup_id, [row.model_dump() for row in data.rows])
    except ParameterLookupValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{lookup_id}/curve-profile", response_model=ParameterLookupCurveProfilePayload)
def get_lookup_curve_profile(lookup_id: int, db: Session = Depends(get_db)):
    try:
        return get_parameter_lookup_curve_profile(db, lookup_id)
    except ParameterLookupValidationError as exc:
        detail = str(exc)
        status_code = 404 if detail == "lookup not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.put("/{lookup_id}/curve-profile", response_model=ParameterLookupCurveProfilePayload)
def put_lookup_curve_profile(
    lookup_id: int,
    data: ParameterLookupCurveProfilePayload,
    db: Session = Depends(get_db),
):
    try:
        return save_parameter_lookup_curve_profile(db, lookup_id, data.model_dump())
    except ParameterLookupValidationError as exc:
        detail = str(exc)
        status_code = 404 if detail == "lookup not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.get("/{lookup_id}/curve-preview", response_model=ParameterLookupCurvePreviewOut)
def get_lookup_curve_preview(lookup_id: int, db: Session = Depends(get_db)):
    try:
        return build_parameter_lookup_curve_preview(db, lookup_id)
    except ParameterLookupValidationError as exc:
        detail = str(exc)
        status_code = 404 if detail == "lookup not found" else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.post("/import/preview", response_model=ParameterLookupImportPreviewOut)
def preview_parameter_lookup_import(data: ParameterLookupImportPreviewRequest):
    return build_parameter_lookup_import_preview(data.rows, sheet_name=data.sheet_name)
