from pydantic import BaseModel
from datetime import time
from typing import Optional


class TimeslotBase(BaseModel):
    day_of_week: str
    period_number: int
    start_time: time
    end_time: time


class TimeslotCreate(TimeslotBase):
    pass


class TimeslotUpdate(BaseModel):
    day_of_week: Optional[str] = None
    period_number: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class TimeslotRead(TimeslotBase):
    id: int

    class Config:
        from_attributes = True


class BulkTimeslotCreate(BaseModel):
    periods_per_day: int = 5
    start_hour: int = 9
    period_duration_minutes: int = 60
