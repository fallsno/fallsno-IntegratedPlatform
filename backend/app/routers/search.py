from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.search_service import search_families, get_suggestions, record_search
from app.schemas import SearchSuggestion

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/")
def search(keyword: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    record_search(db, keyword)
    return search_families(db, keyword)

@router.get("/suggestions", response_model=List[SearchSuggestion])
def suggestions(prefix: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return get_suggestions(db, prefix)
