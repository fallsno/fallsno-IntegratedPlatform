from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import EquipmentCategory, EquipmentItem
from app.schemas import (
    EquipmentCategoryCreate,
    EquipmentCategoryOut,
    EquipmentItemCreate,
    EquipmentItemOut,
    EquipmentRecommendRequest,
    EquipmentRecommendation,
)

router = APIRouter(prefix="/equipment", tags=["equipment"])

@router.get("/categories", response_model=List[EquipmentCategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(EquipmentCategory).all()

@router.post("/categories", response_model=EquipmentCategoryOut)
def create_category(data: EquipmentCategoryCreate, db: Session = Depends(get_db)):
    db_obj = EquipmentCategory(**data.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/items", response_model=List[EquipmentItemOut])
def list_items(category_id: int = None, query_str: str = None, db: Session = Depends(get_db)):
    query = db.query(EquipmentItem)
    if category_id:
        query = query.filter(EquipmentItem.category_id == category_id)
    if query_str:
        # Check both exact match and LIKE match
        # Try exact match first or LIKE
        from sqlalchemy import or_
        query = query.filter(or_(
            EquipmentItem.model_name == query_str,
            EquipmentItem.model_name.ilike(f"%{query_str}%")
        ))
    return query.all()

@router.post("/items", response_model=EquipmentItemOut)
def create_item(data: EquipmentItemCreate, db: Session = Depends(get_db)):
    db_obj = EquipmentItem(**data.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.post("/items/bulk", response_model=List[EquipmentItemOut])
def create_items_bulk(data_list: List[EquipmentItemCreate], db: Session = Depends(get_db)):
    db_objs = [EquipmentItem(**data.dict()) for data in data_list]
    db.add_all(db_objs)
    db.commit()
    for obj in db_objs:
        db.refresh(obj)
    return db_objs

@router.post("/recommend", response_model=List[EquipmentRecommendation])
def recommend_equipment(request: EquipmentRecommendRequest, db: Session = Depends(get_db)):
    # 1. 查找分类
    category = db.query(EquipmentCategory).filter(EquipmentCategory.code == request.category_code).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    reqs = request.requirements
    min_speed = reqs.target_speed_rpm * (1 - reqs.speed_tolerance_percent / 100.0)
    max_speed = reqs.target_speed_rpm * (1 + reqs.speed_tolerance_percent / 100.0)

    # 2. 获取该分类下的所有设备（在内存中进行复杂过滤和打分）
    items = db.query(EquipmentItem).filter(EquipmentItem.category_id == category.id).all()

    candidates = []
    for item in items:
        specs = item.specs
        if not specs:
            continue
            
        power = specs.get("power_kw", 0)
        speed = specs.get("speed_rpm", 0)
        torque = specs.get("torque_nm", 0)

        # 硬性过滤：功率必须达标，扭矩必须达标，转速必须在容差范围内
        if power >= reqs.min_power_kw and torque >= reqs.min_torque_nm and min_speed <= speed <= max_speed:
            
            # 智能打分 (Scoring)
            # 1. 转速贴合度 (满分 50)：越接近目标转速得分越高
            speed_diff_ratio = abs(speed - reqs.target_speed_rpm) / reqs.target_speed_rpm
            speed_score = max(0, 50 * (1 - speed_diff_ratio / (reqs.speed_tolerance_percent / 100.0)))

            # 2. 功率经济性 (满分 30)：功率大于需求，但余量越小越好（避免大马拉小车）
            power_diff_ratio = (power - reqs.min_power_kw) / reqs.min_power_kw
            # 如果功率是需求的2倍以上，经济性得分为0
            power_score = max(0, 30 * (1 - min(power_diff_ratio, 1.0))) 

            # 3. 安全系数/扭矩余量 (满分 20)：扭矩余量越大越安全，但超过50%余量后不再加分
            torque_margin = (torque - reqs.min_torque_nm) / reqs.min_torque_nm
            torque_score = min(20, 20 * (torque_margin / 0.5))

            total_score = speed_score + power_score + torque_score

            # 生成自然语言建议
            reason = f"匹配度 {total_score:.1f}分。转速偏差 {speed_diff_ratio*100:.1f}%，功率冗余 {power_diff_ratio*100:.1f}%。"
            if speed_score >= 45 and power_score >= 20:
                reason = "极佳推荐：" + reason
            elif total_score >= 80:
                reason = "优选推荐：" + reason
            else:
                reason = "备选方案：" + reason

            candidates.append(EquipmentRecommendation(
                item=EquipmentItemOut.from_orm(item),
                score=total_score,
                match_details={
                    "speed_score": speed_score,
                    "power_score": power_score,
                    "torque_score": torque_score
                },
                reason=reason
            ))

    # 按总分降序排列
    candidates.sort(key=lambda x: x.score, reverse=True)

    # 返回 Top 3
    return candidates[:3]
