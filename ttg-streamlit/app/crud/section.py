from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.crud.base import CRUDBase
from app.models.section import Section
from app.models.associations import SectionSubject


class CRUDSection(CRUDBase):
    def __init__(self):
        super().__init__(Section)

    def get_subjects(self, db: Session, section_id: int) -> List[SectionSubject]:
        return db.query(SectionSubject).options(
            joinedload(SectionSubject.subject),
            joinedload(SectionSubject.faculty)
        ).filter(SectionSubject.section_id == section_id).all()

    def assign_subject(self, db: Session, section_id: int, subject_id: int, faculty_id: Optional[int]) -> SectionSubject:
        existing = db.query(SectionSubject).filter(
            SectionSubject.section_id == section_id,
            SectionSubject.subject_id == subject_id
        ).first()
        if existing:
            existing.faculty_id = faculty_id
            db.commit()
            db.refresh(existing)
            return existing
        ss = SectionSubject(section_id=section_id, subject_id=subject_id, faculty_id=faculty_id)
        db.add(ss)
        db.commit()
        db.refresh(ss)
        return ss

    def remove_subject(self, db: Session, section_id: int, subject_id: int) -> bool:
        deleted = db.query(SectionSubject).filter(
            SectionSubject.section_id == section_id,
            SectionSubject.subject_id == subject_id
        ).delete(synchronize_session=False)
        db.commit()
        return deleted > 0


crud_section = CRUDSection()
