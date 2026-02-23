from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.crud.faculty import crud_faculty
from app.schemas.faculty import FacultyRead, FacultyCreate, FacultyUpdate, AvailabilityUpdate
from app.models.timetable import TimetableEntry, TimetableGeneration
from app.schemas.timetable import TimetableEntryRead

router = APIRouter(prefix="/api/faculty", tags=["faculty"])


@router.get("", response_model=List[FacultyRead])
def get_faculty(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_faculty.get_all(db, skip=skip, limit=limit)


@router.post("", response_model=FacultyRead)
def create_faculty(data: FacultyCreate, db: Session = Depends(get_db)):
    return crud_faculty.create(db, data)


@router.get("/{faculty_id}", response_model=FacultyRead)
def get_faculty_by_id(faculty_id: int, db: Session = Depends(get_db)):
    obj = crud_faculty.get(db, faculty_id)
    if not obj:
        raise HTTPException(404, "Faculty not found")
    return obj


@router.put("/{faculty_id}", response_model=FacultyRead)
def update_faculty(faculty_id: int, data: FacultyUpdate, db: Session = Depends(get_db)):
    obj = crud_faculty.get(db, faculty_id)
    if not obj:
        raise HTTPException(404, "Faculty not found")
    return crud_faculty.update(db, obj, data)


@router.delete("/{faculty_id}")
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    obj = crud_faculty.delete(db, faculty_id)
    if not obj:
        raise HTTPException(404, "Faculty not found")
    return {"ok": True}


@router.get("/{faculty_id}/availability")
def get_availability(faculty_id: int, db: Session = Depends(get_db)):
    obj = crud_faculty.get(db, faculty_id)
    if not obj:
        raise HTTPException(404, "Faculty not found")
    blocked = crud_faculty.get_availability(db, faculty_id)
    return {"faculty_id": faculty_id, "blocked_timeslot_ids": blocked}


@router.put("/{faculty_id}/availability")
def set_availability(faculty_id: int, data: AvailabilityUpdate, db: Session = Depends(get_db)):
    obj = crud_faculty.get(db, faculty_id)
    if not obj:
        raise HTTPException(404, "Faculty not found")
    blocked = crud_faculty.set_availability(db, faculty_id, data.blocked_timeslot_ids)
    return {"faculty_id": faculty_id, "blocked_timeslot_ids": blocked}


@router.get("/{faculty_id}/timetable", response_model=List[TimetableEntryRead])
def get_faculty_timetable(faculty_id: int, db: Session = Depends(get_db)):
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
        TimetableEntry.faculty_id == faculty_id,
        TimetableEntry.generation_id == active_gen.id
    ).all()
    return entries
