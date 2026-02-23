from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.timetable import TimetableGeneration, TimetableEntry
from app.schemas.timetable import TimetableGenerationRead, TimetableEntryRead
from app.scheduler.timetable_builder import run_generation

router = APIRouter(prefix="/api/timetable", tags=["timetable"])


@router.post("/generate", response_model=TimetableGenerationRead)
def generate_timetable(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    generation = TimetableGeneration(status="pending")
    db.add(generation)
    db.commit()
    db.refresh(generation)
    background_tasks.add_task(run_generation, db, generation.id)
    return generation


@router.get("/status/{generation_id}", response_model=TimetableGenerationRead)
def get_status(generation_id: str, db: Session = Depends(get_db)):
    gen = db.query(TimetableGeneration).filter(TimetableGeneration.id == generation_id).first()
    if not gen:
        raise HTTPException(404, "Generation not found")
    return gen


@router.get("", response_model=List[TimetableGenerationRead])
def list_generations(db: Session = Depends(get_db)):
    return db.query(TimetableGeneration).order_by(TimetableGeneration.created_at.desc()).all()


@router.get("/{generation_id}", response_model=List[TimetableEntryRead])
def get_generation_entries(generation_id: str, db: Session = Depends(get_db)):
    gen = db.query(TimetableGeneration).filter(TimetableGeneration.id == generation_id).first()
    if not gen:
        raise HTTPException(404, "Generation not found")
    entries = db.query(TimetableEntry).options(
        joinedload(TimetableEntry.section),
        joinedload(TimetableEntry.subject),
        joinedload(TimetableEntry.faculty),
        joinedload(TimetableEntry.room),
        joinedload(TimetableEntry.timeslot)
    ).filter(TimetableEntry.generation_id == generation_id).all()
    return entries


@router.post("/{generation_id}/activate", response_model=TimetableGenerationRead)
def activate_generation(generation_id: str, db: Session = Depends(get_db)):
    gen = db.query(TimetableGeneration).filter(TimetableGeneration.id == generation_id).first()
    if not gen:
        raise HTTPException(404, "Generation not found")
    if gen.status != "success":
        raise HTTPException(400, "Can only activate successful generations")
    db.query(TimetableGeneration).update({"is_active": False})
    gen.is_active = True
    db.commit()
    db.refresh(gen)
    return gen


@router.delete("/{generation_id}")
def delete_generation(generation_id: str, db: Session = Depends(get_db)):
    gen = db.query(TimetableGeneration).filter(TimetableGeneration.id == generation_id).first()
    if not gen:
        raise HTTPException(404, "Generation not found")
    db.delete(gen)
    db.commit()
    return {"ok": True}
