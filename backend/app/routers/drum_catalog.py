from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DrumGenerateVersionsOut, DrumTreeTypeOut
from app.services.drum_catalog import DrumCatalogError, build_drum_tree, create_family_versions


router = APIRouter(prefix="/drum-catalog", tags=["drum-catalog"])


@router.get("/tree", response_model=list[DrumTreeTypeOut])
def get_drum_tree(db: Session = Depends(get_db)):
    return build_drum_tree(db)


@router.post("/families/{family_id}/generate-versions", response_model=DrumGenerateVersionsOut)
def generate_family_versions(family_id: int, db: Session = Depends(get_db)):
    try:
        return create_family_versions(db, family_id)
    except DrumCatalogError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
