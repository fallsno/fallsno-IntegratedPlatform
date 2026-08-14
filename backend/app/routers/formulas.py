from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import FormulaLibrary
from app.schemas import FormulaCreate, FormulaUpdate, FormulaOut, FormulaEvaluateRequest, FormulaEvaluateResult
from app.services.formula_engine import FormulaEngineError, evaluate_formula_expression
from app.services.formula_library import (
    FormulaLibraryValidationError,
    serialize_formula_record,
    validate_formula_payload,
)

router = APIRouter(prefix="/formulas", tags=["formulas"])

@router.get("/", response_model=List[FormulaOut])
def list_formulas(category: str = None, db: Session = Depends(get_db)):
    q = db.query(FormulaLibrary)
    if category:
        q = q.filter(FormulaLibrary.category == category)
    return [serialize_formula_record(item) for item in q.all()]

@router.post("/", response_model=FormulaOut)
def create_formula(data: FormulaCreate, db: Session = Depends(get_db)):
    try:
        payload = validate_formula_payload(data.model_dump())
    except FormulaLibraryValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    formula = FormulaLibrary(**payload)
    db.add(formula)
    db.commit()
    db.refresh(formula)
    return serialize_formula_record(formula)

@router.put("/{formula_id}", response_model=FormulaOut)
def update_formula(formula_id: int, data: FormulaUpdate, db: Session = Depends(get_db)):
    f = db.query(FormulaLibrary).get(formula_id)
    if not f:
        raise HTTPException(404)

    try:
        payload = validate_formula_payload(data.model_dump(exclude_unset=True), partial=True)
    except FormulaLibraryValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    for k, v in payload.items():
        setattr(f, k, v)
    db.commit()
    db.refresh(f)
    return serialize_formula_record(f)

@router.post("/evaluate", response_model=FormulaEvaluateResult)
def evaluate_formula(data: FormulaEvaluateRequest):
    try:
        return evaluate_formula_expression(
            data.expression,
            data.scope,
            available_variable_names=data.available_variable_names,
            precision=data.precision,
        )
    except FormulaEngineError as exc:
        raise HTTPException(status_code=400, detail={
            "code": exc.code,
            "message": str(exc),
            "details": exc.details,
        }) from exc

@router.delete("/{formula_id}")
def delete_formula(formula_id: int, db: Session = Depends(get_db)):
    f = db.query(FormulaLibrary).get(formula_id)
    if f:
        db.delete(f)
        db.commit()
    return {"ok": True}
