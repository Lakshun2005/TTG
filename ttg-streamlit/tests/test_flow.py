import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.subject import Subject
from app.models.faculty import Faculty
from app.models.room import Room
from app.models.section import Section
from app.models.timeslot import Timeslot
from app.models.associations import SectionSubject, FacultySubject
from app.models.timetable import TimetableGeneration, TimetableEntry
from app.scheduler.timetable_builder import run_generation

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_full_flow(db):
    # 1. Setup Base Entities
    fac1 = Faculty(name="Alan Turing", subject_specialization="Math", department="Science")
    fac2 = Faculty(name="Grace Hopper", subject_specialization="CompSci", department="Engineering")
    db.add_all([fac1, fac2])
    
    sub1 = Subject(name="Calculus", code="MAT101", credits=3, hours_per_week=2, semester=1, requires_lab=False)
    sub2 = Subject(name="Programming", code="CS101", credits=4, hours_per_week=2, semester=1, requires_lab=True)
    db.add_all([sub1, sub2])
    
    room1 = Room(name="Room A", capacity=100, room_type="classroom")
    room2 = Room(name="Lab 1", capacity=50, room_type="lab")
    db.add_all([room1, room2])
    
    sec1 = Section(name="Section A", semester=1, student_count=40)
    db.add(sec1)
    
    ts1 = Timeslot(day_of_week="Monday", period_number=1, start_time=datetime.time(9,0), end_time=datetime.time(10,0))
    ts2 = Timeslot(day_of_week="Monday", period_number=2, start_time=datetime.time(10,0), end_time=datetime.time(11,0))
    ts3 = Timeslot(day_of_week="Tuesday", period_number=1, start_time=datetime.time(9,0), end_time=datetime.time(10,0))
    ts4 = Timeslot(day_of_week="Tuesday", period_number=2, start_time=datetime.time(10,0), end_time=datetime.time(11,0))
    db.add_all([ts1, ts2, ts3, ts4])
    db.commit()

    # 2. Associations (Faculty mapping)
    db.add(FacultySubject(faculty_id=fac1.id, subject_id=sub1.id))
    db.add(FacultySubject(faculty_id=fac2.id, subject_id=sub2.id))

    # assignments
    db.add(SectionSubject(section_id=sec1.id, subject_id=sub1.id, faculty_id=fac1.id))
    db.add(SectionSubject(section_id=sec1.id, subject_id=sub2.id, faculty_id=fac2.id))
    db.commit()

    # 3. Generate Timetable
    gen = TimetableGeneration(status="pending")
    db.add(gen)
    db.commit()
    
    run_generation(db, gen.id)
    
    # 4. Assert Results
    db.refresh(gen)
    assert gen.status == "success"
    
    entries = db.query(TimetableEntry).filter_by(generation_id=gen.id).all()
    # Math = 2 hours, CompSci = 2 hours -> Total 4 entries
    assert len(entries) == 4
    
    assigned_slots = [(e.timeslot_id, e.room_id) for e in entries]
    # Check no duplicate timeslot for the section
    ts_only = [e.timeslot_id for e in entries]
    assert len(ts_only) == len(set(ts_only))

    # Verify room types
    for e in entries:
        if e.subject_id == sub1.id:
            assert e.room_id == room1.id
        elif e.subject_id == sub2.id:
            assert e.room_id == room2.id
