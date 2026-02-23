from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.subject import SubjectRead
from app.schemas.faculty import FacultyRead


class SectionBase(BaseModel):
    name: str
    semester: int
    student_count: int


class SectionCreate(SectionBase):
    pass


class SectionUpdate(BaseModel):
    name: Optional[str] = None
    semester: Optional[int] = None
    student_count: Optional[int] = None


class SectionRead(SectionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SectionSubjectAssign(BaseModel):
    subject_id: int
    faculty_id: Optional[int] = None


class SectionSubjectRead(BaseModel):
    id: int
    section_id: int
    subject_id: int
    faculty_id: Optional[int]
    subject: SubjectRead
    faculty: Optional[FacultyRead]

    class Config:
        from_attributes = True
