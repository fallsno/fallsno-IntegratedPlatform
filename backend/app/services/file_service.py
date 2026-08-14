import os
import uuid
import shutil
from datetime import datetime
from fastapi import UploadFile

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
    'word': ['.doc', '.docx'],
    'excel': ['.xls', '.xlsx', '.csv'],
    'pdf': ['.pdf'],
}

def get_file_category(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    for cat, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts: return cat
    return 'other'

async def save_upload_file(upload_file: UploadFile, version_id: int) -> dict:
    ext = os.path.splitext(upload_file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    date_str = datetime.now().strftime("%Y%m")
    upload_path = os.path.join(UPLOAD_DIR, str(version_id), date_str)
    os.makedirs(upload_path, exist_ok=True)
    file_path = os.path.join(upload_path, unique_name)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return {
        "file_name": upload_file.filename,
        "file_path": file_path,
        "file_type": upload_file.content_type,
        "file_size": os.path.getsize(file_path),
        "file_category": get_file_category(upload_file.filename)
    }

def delete_upload_file(file_path: str) -> bool:
    try:
        if os.path.exists(file_path): os.remove(file_path); return True
    except: pass
    return False
