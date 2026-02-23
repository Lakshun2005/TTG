from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.subject import crud_subject
from app.schemas.subject import SubjectRead, SubjectCreate, SubjectUpdate

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


@router.get("", response_model=List[SubjectRead])
def get_subjects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_subject.get_all(db, skip=skip, limit=limit)


@router.post("", response_model=SubjectRead)
def create_subject(data: SubjectCreate, db: Session = Depends(get_db)):
    return crud_subject.create(db, data)


@router.get("/{subject_id}", response_model=SubjectRead)
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    obj = crud_subject.get(db, subject_id)
    if not obj:
        raise HTTPException(404, "Subject not found")
    return obj


@router.put("/{subject_id}", response_model=SubjectRead)
def update_subject(subject_id: int, data: SubjectUpdate, db: Session = Depends(get_db)):
    obj = crud_subject.get(db, subject_id)
    if not obj:
        raise HTTPException(404, "Subject not found")
    return crud_subject.update(db, obj, data)


@router.delete("/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    obj = crud_subject.delete(db, subject_id)
    if not obj:
        raise HTTPException(404, "Subject not found")
    return {"ok": True}
