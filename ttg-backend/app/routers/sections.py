from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.crud.section import crud_section
from app.schemas.section import SectionRead, SectionCreate, SectionUpdate, SectionSubjectAssign, SectionSubjectRead
from app.models.associations import SectionSubject
from app.models.timetable import TimetableEntry, TimetableGeneration
from app.schemas.timetable import TimetableEntryRead

router = APIRouter(prefix="/api/sections", tags=["sections"])


@router.get("", response_model=List[SectionRead])
def get_sections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_section.get_all(db, skip=skip, limit=limit)


@router.post("", response_model=SectionRead)
def create_section(data: SectionCreate, db: Session = Depends(get_db)):
    return crud_section.create(db, data)


@router.get("/{section_id}", response_model=SectionRead)
def get_section(section_id: int, db: Session = Depends(get_db)):
    obj = crud_section.get(db, section_id)
    if not obj:
        raise HTTPException(404, "Section not found")
    return obj


@router.put("/{section_id}", response_model=SectionRead)
def update_section(section_id: int, data: SectionUpdate, db: Session = Depends(get_db)):
    obj = crud_section.get(db, section_id)
    if not obj:
        raise HTTPException(404, "Section not found")
    return crud_section.update(db, obj, data)


@router.delete("/{section_id}")
def delete_section(section_id: int, db: Session = Depends(get_db)):
    obj = crud_section.delete(db, section_id)
    if not obj:
        raise HTTPException(404, "Section not found")
    return {"ok": True}


@router.get("/{section_id}/subjects", response_model=List[SectionSubjectRead])
def get_section_subjects(section_id: int, db: Session = Depends(get_db)):
    obj = crud_section.get(db, section_id)
    if not obj:
        raise HTTPException(404, "Section not found")
    return crud_section.get_subjects(db, section_id)


@router.post("/{section_id}/subjects", response_model=SectionSubjectRead)
def assign_subject(section_id: int, data: SectionSubjectAssign, db: Session = Depends(get_db)):
    obj = crud_section.get(db, section_id)
    if not obj:
        raise HTTPException(404, "Section not found")
    result = crud_section.assign_subject(db, section_id, data.subject_id, data.faculty_id)
    return db.query(SectionSubject).options(
        joinedload(SectionSubject.subject),
        joinedload(SectionSubject.faculty)
    ).filter(SectionSubject.id == result.id).first()


@router.delete("/{section_id}/subjects/{subject_id}")
def remove_subject(section_id: int, subject_id: int, db: Session = Depends(get_db)):
    success = crud_section.remove_subject(db, section_id, subject_id)
    if not success:
        raise HTTPException(404, "Assignment not found")
    return {"ok": True}


@router.get("/{section_id}/timetable", response_model=List[TimetableEntryRead])
def get_section_timetable(section_id: int, db: Session = Depends(get_db)):
    active_gen = db.query(TimetableGeneration).filter(
        TimetableGeneration.is_active == True
    ).first()
    if not active_gen:
        return []
    entries = db.query(TimetableEntry).options(
        joinedload(TimetableEntry.section),
        joinedload(TimetableEntry.subject),
        joinedload(TimetableEntry.faculty),
        joinedload(TimetableEntry.room),
        joinedload(TimetableEntry.timeslot)
    ).filter(
        TimetableEntry.section_id == section_id,
        TimetableEntry.generation_id == active_gen.id
    ).all()
    return entries
