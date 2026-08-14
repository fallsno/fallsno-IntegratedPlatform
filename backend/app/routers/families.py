from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import ModelFamily, ModelAlias, ModelVersion
from app.schemas import FamilyCreate, FamilyOut, VersionCreate, VersionOut, AliasOut
from app.services.search_service import record_search

router = APIRouter(prefix="/families", tags=["families"])

@router.get("/", response_model=List[FamilyOut])
def list_families(
    category: Optional[str] = None, 
    product_type_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    q = db.query(ModelFamily)
    if category: q = q.filter(ModelFamily.category == category)
    if product_type_id: q = q.filter(ModelFamily.product_type_id == product_type_id)
    return q.order_by(ModelFamily.family_code).all()

@router.post("/", response_model=FamilyOut)
def create_family(family: FamilyCreate, db: Session = Depends(get_db)):
    # 服务端校验
    if not family.family_code or not family.family_code.strip():
        raise HTTPException(status_code=400, detail="主代号不能为空")
    if not family.family_name or not family.family_name.strip():
        raise HTTPException(status_code=400, detail="名称不能为空")
    
    # 唯一性校验
    existing = db.query(ModelFamily).filter(ModelFamily.family_code == family.family_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="主代号已存在")
    
    db_family = ModelFamily(**family.dict())
    db.add(db_family)
    db.commit()
    db.refresh(db_family)
    return db_family

@router.get("/{family_id}", response_model=FamilyOut)
def get_family(family_id: int, db: Session = Depends(get_db)):
    f = db.query(ModelFamily).filter(ModelFamily.id == family_id).first()
    if not f: raise HTTPException(404, "Family not found")
    return f

@router.put("/{family_id}", response_model=FamilyOut)
def update_family(family_id: int, family_update: FamilyCreate, db: Session = Depends(get_db)):
    # 同样进行非空校验
    if not family_update.family_code or not family_update.family_code.strip():
        raise HTTPException(status_code=400, detail="主代号不能为空")
    if not family_update.family_name or not family_update.family_name.strip():
        raise HTTPException(status_code=400, detail="名称不能为空")
    
    family = db.query(ModelFamily).filter(ModelFamily.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="型号不存在")
    
    # 检查主代号是否与其他记录冲突（排除自身）
    existing = db.query(ModelFamily).filter(
        ModelFamily.family_code == family_update.family_code,
        ModelFamily.id != family_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="主代号已被其他型号使用")
    
    for key, value in family_update.dict().items():
        setattr(family, key, value)
    db.commit()
    db.refresh(family)
    return family

@router.delete("/{family_id}")
def delete_family(family_id: int, db: Session = Depends(get_db)):
    family = db.query(ModelFamily).filter(ModelFamily.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="型号不存在")
    # 注意：如果外键设置了级联删除，以下两行可省略；若无级联，需手动清理
    db.query(ModelVersion).filter(ModelVersion.family_id == family_id).delete()
    db.query(ModelAlias).filter(ModelAlias.family_id == family_id).delete()
    db.delete(family)
    db.commit()
    return {"message": "删除成功"}

@router.post("/{family_id}/aliases")
def add_alias(family_id: int, alias_code: str, alias_type: str = 'old', db: Session = Depends(get_db)):
    f = db.query(ModelFamily).filter(ModelFamily.id == family_id).first()
    if not f: raise HTTPException(404, "Family not found")
    alias = ModelAlias(family_id=family_id, alias_code=alias_code, alias_type=alias_type)
    db.add(alias)
    db.commit()
    return {"ok": True}

@router.get("/{family_id}/versions", response_model=List[VersionOut])
def list_versions(family_id: int, db: Session = Depends(get_db)):
    return db.query(ModelVersion).filter(ModelVersion.family_id == family_id).order_by(ModelVersion.created_at.desc()).all()

@router.post("/{family_id}/versions", response_model=VersionOut)
def create_version(family_id: int, version: VersionCreate, db: Session = Depends(get_db)):
    # ✅ 新增：校验版本号非空
    if not version.version_code or not version.version_code.strip():
        raise HTTPException(status_code=400, detail="版本号不能为空")
    
    f = db.query(ModelFamily).filter(ModelFamily.id == family_id).first()
    if not f:
        raise HTTPException(404, "Family not found")
    
    # ✅ 可选：检查同一型号下版本号是否重复
    existing = db.query(ModelVersion).filter(
        ModelVersion.family_id == family_id,
        ModelVersion.version_code == version.version_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该版本号已存在")
    
    try:
        db_version = ModelVersion(family_id=family_id, **version.dict(exclude={'family_id'}))
        db.add(db_version)
        db.flush() # flush to get db_version.id
        
        # 自动为新版本挂载默认公式模板
        from app.models import ModelWorkbenchConfig, FormulaTemplate
        template_id = None
        if f.default_template_code:
            template = db.query(FormulaTemplate).filter(FormulaTemplate.template_code == f.default_template_code).first()
            if template:
                template_id = template.id
        
        if not template_id and f.product_type_id:
            # 尝试查找同产品类型的活跃模板
            template = db.query(FormulaTemplate).filter(
                FormulaTemplate.product_type_id == f.product_type_id,
                FormulaTemplate.is_active == True
            ).first()
            if template:
                template_id = template.id
                
        if not template_id:
            # 兜底：任意一个活跃模板
            template = db.query(FormulaTemplate).filter(FormulaTemplate.is_active == True).first()
            if template:
                template_id = template.id
                
        config = ModelWorkbenchConfig(
            model_version_id=db_version.id,
            formula_template_id=template_id
        )
        db.add(config)
        
        db.commit()
        db.refresh(db_version)
        return db_version
    except Exception as e:
        db.rollback()
        print(f"Error creating version: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))