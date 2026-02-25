from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    semester = Column(Integer, nullable=False)
    student_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    section_subjects = relationship("SectionSubject", back_populates="section", cascade="all, delete-orphan")
    timetable_entries = relationship("TimetableEntry", back_populates="section")
