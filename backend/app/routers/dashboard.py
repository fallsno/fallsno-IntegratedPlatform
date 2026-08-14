from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import ProductType, DesignRule, DesignChange, OperationHistory
from typing import Dict, Any, List

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    product_count = db.query(ProductType).count()
    rule_count = db.query(DesignRule).filter(DesignRule.is_active == True).count()
    pending_changes = db.query(DesignChange).filter(DesignChange.status == "submitted").count()
    
    # 模拟健康度计算 (实际可根据违规记录数反向计算)
    health_score = 95
    
    return {
        "productCount": product_count,
        "ruleCount": rule_count,
        "pendingChanges": pending_changes,
        "healthScore": health_score
    }

@router.get("/activities")
def get_recent_activities(db: Session = Depends(get_db), limit: int = 10):
    activities = db.query(OperationHistory).order_by(OperationHistory.created_at.desc()).limit(limit).all()
    
    result = []
    for act in activities:
        type_map = {
            "create": "primary",
            "update": "success",
            "delete": "danger",
            "clone": "warning",
            "reorder": "info"
        }
        
        module_name_map = {
            "product_types": "产品项目",
            "product_components": "部件结构",
            "design_flows": "设计流程",
            "formulas": "计算公式"
        }
        
        module_display = module_name_map.get(act.module, act.module)
        operation_display = "更新了" if act.operation_type == "update" else \
                            "创建了" if act.operation_type == "create" else \
                            "删除了" if act.operation_type == "delete" else \
                            "克隆了" if act.operation_type == "clone" else "移动了"
        
        result.append({
            "content": f"{operation_display} {module_display} (ID: {act.entity_id})",
            "time": act.created_at.strftime("%Y-%m-%d %H:%M"),
            "type": type_map.get(act.operation_type, "info")
        })
        
    # 如果没有活动记录，返回一些预置数据
    if not result:
        result = [
            { "content": "系统初始化完成", "time": "2026-05-01 09:00", "type": "info" }
        ]
        
    return result
