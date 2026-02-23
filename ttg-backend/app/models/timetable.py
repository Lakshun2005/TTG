import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


# Use String(36) for UUID — works with both SQLite and PostgreSQL
class TimetableGeneration(Base):
    __tablename__ = "timetable_generations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="pending")  # pending, running, success, failed
    is_active = Column(Boolean, default=False)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    entries = relationship("TimetableEntry", back_populates="generation", cascade="all, delete-orphan")


class TimetableEntry(Base):
    __tablename__ = "timetable_entries"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    timeslot_id = Column(Integer, ForeignKey("timeslots.id"), nullable=False)
    generation_id = Column(String(36), ForeignKey("timetable_generations.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("room_id", "timeslot_id", "generation_id", name="uq_room_timeslot_gen"),
        UniqueConstraint("faculty_id", "timeslot_id", "generation_id", name="uq_faculty_timeslot_gen"),
        UniqueConstraint("section_id", "timeslot_id", "generation_id", name="uq_section_timeslot_gen"),
    )

    section = relationship("Section", back_populates="timetable_entries")
    subject = relationship("Subject", back_populates="timetable_entries")
    faculty = relationship("Faculty", back_populates="timetable_entries")
    room = relationship("Room", back_populates="timetable_entries")
    timeslot = relationship("Timeslot", back_populates="timetable_entries")
    generation = relationship("TimetableGeneration", back_populates="entries")
