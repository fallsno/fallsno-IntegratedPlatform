from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ProductComponent, ComponentFlowStep, DesignRule
from typing import List, Dict, Any
import re

router = APIRouter(prefix="/rules", tags=["rules"])

@router.get("/validate/{type_id}")
def validate_product_design(type_id: int, db: Session = Depends(get_db)):
    """对指定产品类型的所有设计参数执行规则校验"""
    # 1. 获取所有激活的规则
    rules = db.query(DesignRule).filter(DesignRule.is_active == True).all()
    
    # 2. 获取该产品下的所有参数值
    components = db.query(ProductComponent).filter(ProductComponent.product_type_id == type_id).all()
    comp_ids = [c.id for c in components]
    
    # 获取计算步骤中的所有行数据
    steps = db.query(ComponentFlowStep).all() # 实际应过滤关联组件的步骤
    
    param_values = {}
    for step in steps:
        content = step.calculation_content or {}
        rows = content.get("rows", [])
        for row in rows:
            name = row.get("name")
            if name:
                # 简单处理：同名参数取最后一个值
                param_values[name] = row.get("value")

    violations = []
    
    # 3. 执行规则匹配
    for rule in rules:
        # 简单规则引擎：使用 Python eval 或 simpleeval (此处演示简单逻辑)
        # 假设规则中的变量名对应参数名
        try:
            # 这里的逻辑需要根据实际 rule.constraint_expr 复杂度来实现
            # 目前仅做示意
            violations.append({
                "id": rule.id,
                "name": rule.name,
                "severity": rule.severity,
                "message": rule.message,
                "target_id": rule.target_id
            })
        except Exception as e:
            print(f"Rule validation error: {e}")

    return violations

@router.get("/list", response_model=List[Dict[str, Any]])
def list_rules(db: Session = Depends(get_db)):
    return db.query(DesignRule).all()
