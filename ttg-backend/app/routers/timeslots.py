from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.timeslot import crud_timeslot
from app.schemas.timeslot import TimeslotRead, TimeslotCreate, TimeslotUpdate, BulkTimeslotCreate

router = APIRouter(prefix="/api/timeslots", tags=["timeslots"])


@router.get("", response_model=List[TimeslotRead])
def get_timeslots(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return crud_timeslot.get_all(db, skip=skip, limit=limit)


@router.post("/bulk", response_model=List[TimeslotRead])
def bulk_generate(data: BulkTimeslotCreate, db: Session = Depends(get_db)):
    return crud_timeslot.bulk_generate(db, data.periods_per_day, data.start_hour, data.period_duration_minutes)


@router.post("", response_model=TimeslotRead)
def create_timeslot(data: TimeslotCreate, db: Session = Depends(get_db)):
    return crud_timeslot.create(db, data)


@router.get("/{timeslot_id}", response_model=TimeslotRead)
def get_timeslot(timeslot_id: int, db: Session = Depends(get_db)):
    obj = crud_timeslot.get(db, timeslot_id)
    if not obj:
        raise HTTPException(404, "Timeslot not found")
    return obj


@router.put("/{timeslot_id}", response_model=TimeslotRead)
def update_timeslot(timeslot_id: int, data: TimeslotUpdate, db: Session = Depends(get_db)):
    obj = crud_timeslot.get(db, timeslot_id)
    if not obj:
        raise HTTPException(404, "Timeslot not found")
    return crud_timeslot.update(db, obj, data)


@router.delete("/{timeslot_id}")
def delete_timeslot(timeslot_id: int, db: Session = Depends(get_db)):
    obj = crud_timeslot.delete(db, timeslot_id)
    if not obj:
        raise HTTPException(404, "Timeslot not found")
    return {"ok": True}
