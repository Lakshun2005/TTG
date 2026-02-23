from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.faculty import FacultyRead
from app.schemas.subject import SubjectRead
from app.schemas.room import RoomRead
from app.schemas.section import SectionRead
from app.schemas.timeslot import TimeslotRead


class TimetableGenerationRead(BaseModel):
    id: str
    status: str
    is_active: bool
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TimetableEntryRead(BaseModel):
    id: int
    section: SectionRead
    subject: SubjectRead
    faculty: FacultyRead
    room: RoomRead
    timeslot: TimeslotRead
    generation_id: str

    class Config:
        from_attributes = True
