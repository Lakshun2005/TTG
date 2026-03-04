from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subject_specialization = Column(String, nullable=False)
    department = Column(String, nullable=False)
    max_hours_per_week = Column(Integer, default=20)
    created_at = Column(DateTime, default=datetime.utcnow)

    availability_blocks = relationship("FacultyAvailability", back_populates="faculty", cascade="all, delete-orphan")
    section_subjects = relationship("SectionSubject", back_populates="faculty")
    timetable_entries = relationship("TimetableEntry", back_populates="faculty")
    faculty_subjects = relationship("FacultySubject", back_populates="faculty", cascade="all, delete-orphan")
