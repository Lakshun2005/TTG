from typing import List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.faculty import Faculty
from app.models.associations import FacultyAvailability
from app.schemas.faculty import FacultyCreate, FacultyUpdate


class CRUDFaculty(CRUDBase[Faculty, FacultyCreate, FacultyUpdate]):
    def get_availability(self, db: Session, faculty_id: int) -> List[int]:
        blocks = db.query(FacultyAvailability).filter(
            FacultyAvailability.faculty_id == faculty_id
        ).all()
        return [b.timeslot_id for b in blocks]

    def set_availability(self, db: Session, faculty_id: int, blocked_timeslot_ids: List[int]) -> List[int]:
        db.query(FacultyAvailability).filter(
            FacultyAvailability.faculty_id == faculty_id
        ).delete()
        for ts_id in blocked_timeslot_ids:
            db.add(FacultyAvailability(faculty_id=faculty_id, timeslot_id=ts_id))
        db.commit()
        return blocked_timeslot_ids


crud_faculty = CRUDFaculty(Faculty)
