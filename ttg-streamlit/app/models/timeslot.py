from sqlalchemy import Column, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Timeslot(Base):
    __tablename__ = "timeslots"

    id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(String, nullable=False)   # 'Monday', 'Tuesday', etc.
    period_number = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    __table_args__ = (UniqueConstraint("day_of_week", "period_number", name="uq_day_period"),)

    faculty_blocks = relationship("FacultyAvailability", back_populates="timeslot")
    timetable_entries = relationship("TimetableEntry", back_populates="timeslot")
