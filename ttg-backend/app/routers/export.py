from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.faculty import Faculty
from app.models.section import Section
from app.models.timetable import TimetableEntry, TimetableGeneration
from app.export.pdf_exporter import generate_section_pdf, generate_faculty_pdf
from app.export.excel_exporter import generate_full_excel

router = APIRouter(prefix="/api/export", tags=["export"])


def _load_entries(db: Session, **filters):
    q = db.query(TimetableEntry).options(
        joinedload(TimetableEntry.section),
        joinedload(TimetableEntry.subject),
        joinedload(TimetableEntry.faculty),
        joinedload(TimetableEntry.room),
        joinedload(TimetableEntry.timeslot)
    )
    for attr, val in filters.items():
        q = q.filter(getattr(TimetableEntry, attr) == val)
    return q.all()


@router.get("/pdf/section/{section_id}")
def export_section_pdf(section_id: int, db: Session = Depends(get_db)):
    section = db.get(Section, section_id)
    if not section:
        raise HTTPException(404, "Section not found")

    active_gen = db.query(TimetableGeneration).filter(TimetableGeneration.is_active == True).first()
    if not active_gen:
        raise HTTPException(400, "No active timetable generation")

    entries = _load_entries(db, section_id=section_id, generation_id=active_gen.id)
    pdf_buffer = generate_section_pdf(entries, section.name)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="timetable_{section.name}.pdf"'}
    )


@router.get("/pdf/faculty/{faculty_id}")
def export_faculty_pdf(faculty_id: int, db: Session = Depends(get_db)):
    faculty = db.get(Faculty, faculty_id)
    if not faculty:
        raise HTTPException(404, "Faculty not found")

    active_gen = db.query(TimetableGeneration).filter(TimetableGeneration.is_active == True).first()
    if not active_gen:
        raise HTTPException(400, "No active timetable generation")

    entries = _load_entries(db, faculty_id=faculty_id, generation_id=active_gen.id)
    pdf_buffer = generate_faculty_pdf(entries, faculty.name)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="timetable_{faculty.name}.pdf"'}
    )


@router.get("/excel/{generation_id}")
def export_excel(generation_id: str, db: Session = Depends(get_db)):
    gen = db.query(TimetableGeneration).filter(TimetableGeneration.id == generation_id).first()
    if not gen:
        raise HTTPException(404, "Generation not found")

    entries = _load_entries(db, generation_id=generation_id)
    excel_buffer = generate_full_excel(entries)

    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="timetable_{generation_id}.xlsx"'}
    )
