from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    credits = Column(Integer, nullable=False)
    hours_per_week = Column(Integer, nullable=False)
    requires_lab = Column(Boolean, default=False)
    semester = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    section_subjects = relationship("SectionSubject", back_populates="subject")
    timetable_entries = relationship("TimetableEntry", back_populates="subject")
