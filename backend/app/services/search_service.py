from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import ModelFamily, ModelAlias, SearchHistory
from typing import List
from datetime import datetime

def search_families(db: Session, keyword: str, limit: int = 20) -> List[dict]:
    results = []
    families = db.query(ModelFamily).filter(
        or_(ModelFamily.family_code.ilike(f"%{keyword}%"),
            ModelFamily.family_name.ilike(f"%{keyword}%"))
    ).limit(limit).all()
    alias_families = db.query(ModelFamily).join(ModelAlias).filter(
        ModelAlias.alias_code.ilike(f"%{keyword}%")
    ).distinct().limit(limit).all()
    family_set = {f.id: f for f in families + alias_families}
    for f in list(family_set.values())[:limit]:
        aliases = [a.alias_code for a in f.aliases]
        results.append({
            "type": "family",
            "id": f.id,
            "main_code": f.family_code,
            "name": f.family_name,
            "aliases": aliases,
            "category": f.category
        })
    return results

def get_suggestions(db: Session, prefix: str):
    # 查询型号主代号和旧代号
    families = db.query(ModelFamily).filter(
        (ModelFamily.family_code.ilike(f"%{prefix}%")) |
        (ModelFamily.aliases.any(ModelAlias.alias_code.ilike(f"%{prefix}%")))
    ).limit(10).all()
    
    suggestions = []
    for f in families:
        suggestions.append({
            "term": f.family_code,
            "type": "model",
            "id": f.id,
            "family_id": f.id
        })
        # 可选：也添加别名作为建议项
        for alias in f.aliases:
            if prefix.lower() in alias.alias_code.lower():
                suggestions.append({
                    "term": alias.alias_code,
                    "type": "model",
                    "id": f.id,
                    "family_id": f.id
                })
    
    # 去除重复项（根据 term）
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s["term"] not in seen:
            seen.add(s["term"])
            unique_suggestions.append(s)
    
    return unique_suggestions  # 即使为空也返回 []，不抛出异常

def record_search(db: Session, keyword: str):
    if not keyword or len(keyword) < 2: return
    hist = db.query(SearchHistory).filter(SearchHistory.search_term == keyword).first()
    if hist:
        hist.search_count += 1
        hist.last_searched = datetime.now()
    else:
        db.add(SearchHistory(search_term=keyword))
    db.commit()
