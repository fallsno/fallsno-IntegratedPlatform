from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from app.database import get_db
from app.models import (
    OperationHistory, ProductType, ProductComponent,
    ComponentDesignFlow, ComponentFlowStep
)
from app.schemas import OperationHistoryCreate, OperationHistoryOut

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/", response_model=List[OperationHistoryOut])
def list_history(
    module: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(OperationHistory)
    if module:
        query = query.filter(OperationHistory.module == module)
    return query.order_by(OperationHistory.created_at.desc()).limit(limit).all()


@router.post("/", response_model=OperationHistoryOut)
def create_history(data: OperationHistoryCreate, db: Session = Depends(get_db)):
    history = OperationHistory(**data.dict())
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


@router.post("/undo/{history_id}")
def undo_operation(history_id: int, db: Session = Depends(get_db)):
    """简化版撤回 - 目前主要依赖前端状态管理和已有接口"""
    history = db.query(OperationHistory).get(history_id)
    if not history:
        raise HTTPException(404, detail="History not found")
    
    return {"ok": True, "message": "Undo operation recorded - use module-specific undo for now"}
