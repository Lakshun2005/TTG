from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class RoomType(str, Enum):
    classroom = "classroom"
    lab = "lab"


class RoomBase(BaseModel):
    name: str
    capacity: int
    room_type: RoomType = RoomType.classroom


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    room_type: Optional[RoomType] = None


class RoomRead(RoomBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
