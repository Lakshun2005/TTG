from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SubjectBase(BaseModel):
    name: str
    code: str
    credits: int
    hours_per_week: int
    requires_lab: bool = False
    semester: int


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    credits: Optional[int] = None
    hours_per_week: Optional[int] = None
    requires_lab: Optional[bool] = None
    semester: Optional[int] = None


class SubjectRead(SubjectBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
