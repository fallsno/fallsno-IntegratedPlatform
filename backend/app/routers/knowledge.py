from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import DesignRule, Material
from app.schemas import DesignRuleOut, MaterialOut
from typing import List, Dict, Any

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# --- 规则引擎 API ---
@router.get("/rules", response_model=List[DesignRuleOut])
def get_rules(db: Session = Depends(get_db)):
    try:
        return db.query(DesignRule).filter(DesignRule.is_active == True).all()
    except Exception as e:
        print(f"Error fetching rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rules", response_model=DesignRuleOut)
def create_rule(rule: Dict[str, Any], db: Session = Depends(get_db)):
    db_rule = DesignRule(**rule)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@router.put("/rules/{rule_id}", response_model=DesignRuleOut)
def update_rule(rule_id: int, data: Dict[str, Any], db: Session = Depends(get_db)):
    db_rule = db.query(DesignRule).get(rule_id)
    if not db_rule: raise HTTPException(404)
    for k, v in data.items(): setattr(db_rule, k, v)
    db.commit()
    return db_rule

@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    db_rule = db.query(DesignRule).get(rule_id)
    if db_rule:
        db.delete(db_rule)
        db.commit()
    return {"ok": True}

# --- 材料库 API ---
@router.get("/materials", response_model=List[MaterialOut])
def get_materials(db: Session = Depends(get_db)):
    return db.query(Material).all()

@router.post("/materials", response_model=MaterialOut)
def create_material(material: Dict[str, Any], db: Session = Depends(get_db)):
    db_mat = Material(**material)
    db.add(db_mat)
    db.commit()
    db.refresh(db_mat)
    return db_mat

@router.delete("/materials/{mat_id}")
def delete_material(mat_id: int, db: Session = Depends(get_db)):
    db_mat = db.query(Material).get(mat_id)
    if db_mat:
        db.delete(db_mat)
        db.commit()
    return {"ok": True}

@router.get("/validate")
def validate_params(params: List[Dict[str, Any]], db: Session = Depends(get_db)):
    """校验参数列表是否符合所有激活的规则"""
    rules = db.query(DesignRule).filter(DesignRule.is_active == True).all()
    violations = []
    
    # 这里的逻辑可以根据需求在前端执行（利用 mathjs）或者后端执行
    # 为了演示，我们返回规则定义由前端实时校验
    return {"rules": rules}
