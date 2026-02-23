from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    capacity = Column(Integer, nullable=False)
    room_type = Column(String, nullable=False, default="classroom")  # 'classroom' or 'lab'
    created_at = Column(DateTime, default=datetime.utcnow)

    timetable_entries = relationship("TimetableEntry", back_populates="room")
