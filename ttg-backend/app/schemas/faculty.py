from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class FacultyBase(BaseModel):
    name: str
    email: str
    department: str
    max_hours_per_week: int = 20


class FacultyCreate(FacultyBase):
    pass


class FacultyUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    max_hours_per_week: Optional[int] = None


class FacultyRead(FacultyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AvailabilityUpdate(BaseModel):
    blocked_timeslot_ids: List[int]
