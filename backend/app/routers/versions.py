from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
from app.database import get_db
from app.models import ModelVersion, VersionPart, PartParameter, VersionAttachment, ModelParameterValue
from app.schemas import PartCreate, PartOut, ParameterCreate, ParameterOut, AttachmentOut
from app.services.file_service import save_upload_file, delete_upload_file

router = APIRouter(prefix="/versions", tags=["versions"])

@router.get("/{version_id}/parts", response_model=List[PartOut])
def list_parts(version_id: int, db: Session = Depends(get_db)):
    return db.query(VersionPart).filter(VersionPart.version_id == version_id).order_by(VersionPart.sort_order).all()

@router.post("/{version_id}/parts", response_model=PartOut)
def create_part(version_id: int, part: PartCreate, db: Session = Depends(get_db)):
    # ✅ 新增校验
    if not part.part_category:
        raise HTTPException(status_code=400, detail="部件分类不能为空")
    if not part.part_name or not part.part_name.strip():
        raise HTTPException(status_code=400, detail="部件名称不能为空")
    
    db_part = VersionPart(version_id=version_id, **part.dict(exclude={'version_id'}))
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    return db_part

@router.delete("/parts/{part_id}")
def delete_part(part_id: int, db: Session = Depends(get_db)):
    part = db.query(VersionPart).filter(VersionPart.id == part_id).first()
    if not part: raise HTTPException(404, "Part not found")
    db.delete(part)
    db.commit()
    return {"ok": True}

@router.get("/parts/{part_id}/parameters", response_model=List[ParameterOut])
def list_parameters(part_id: int, db: Session = Depends(get_db)):
    return db.query(PartParameter).filter(PartParameter.part_id == part_id).order_by(PartParameter.sort_order).all()

@router.post("/parts/{part_id}/parameters", response_model=ParameterOut)
def create_parameter(part_id: int, param: ParameterCreate, db: Session = Depends(get_db)):
    db_param = PartParameter(part_id=part_id, **param.dict(exclude={'part_id'}))
    db.add(db_param)
    db.commit()
    db.refresh(db_param)
    return db_param

@router.put("/parameters/{param_id}", response_model=ParameterOut)
def update_parameter(param_id: int, param: ParameterCreate, db: Session = Depends(get_db)):
    db_param = db.query(PartParameter).filter(PartParameter.id == param_id).first()
    if not db_param: raise HTTPException(404, "Parameter not found")
    for k, v in param.dict().items(): setattr(db_param, k, v)
    db.commit()
    db.refresh(db_param)
    return db_param

@router.delete("/parameters/{param_id}")
def delete_parameter(param_id: int, db: Session = Depends(get_db)):
    param = db.query(PartParameter).filter(PartParameter.id == param_id).first()
    if not param: raise HTTPException(404)
    db.delete(param)
    db.commit()
    return {"ok": True}

@router.post("/{version_id}/upload", response_model=AttachmentOut)
async def upload_file(version_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    info = await save_upload_file(file, version_id)
    att = VersionAttachment(version_id=version_id, **info)
    db.add(att)
    db.commit()
    db.refresh(att)
    return att

@router.get("/attachments/{att_id}/download")
def download_file(att_id: int, db: Session = Depends(get_db)):
    att = db.query(VersionAttachment).filter(VersionAttachment.id == att_id).first()
    if not att or not os.path.exists(att.file_path): raise HTTPException(404)
    return FileResponse(att.file_path, media_type=att.file_type, filename=att.file_name)

@router.delete("/attachments/{att_id}")
def delete_file(att_id: int, db: Session = Depends(get_db)):
    att = db.query(VersionAttachment).filter(VersionAttachment.id == att_id).first()
    if not att: raise HTTPException(404)
    delete_upload_file(att.file_path)
    db.delete(att)
    db.commit()
    return {"ok": True}

@router.get("/{version_id}/attachments", response_model=List[AttachmentOut])
def list_attachments(version_id: int, db: Session = Depends(get_db)):
    return db.query(VersionAttachment).filter(VersionAttachment.version_id == version_id).all()


@router.delete("/{version_id}")
def delete_version(version_id: int, db: Session = Depends(get_db)):
    version = db.query(ModelVersion).filter(ModelVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    # 删除关联数据（如果未设置级联）
    db.query(ModelParameterValue).filter(ModelParameterValue.version_id == version_id).delete()
    db.query(PartParameter).filter(
        PartParameter.part_id.in_(
            db.query(VersionPart.id).filter(VersionPart.version_id == version_id)
        )
    ).delete(synchronize_session=False)
    db.query(VersionPart).filter(VersionPart.version_id == version_id).delete()
    db.query(VersionAttachment).filter(VersionAttachment.version_id == version_id).delete()
    
    db.delete(version)
    db.commit()
    return {"message": "版本已删除"}