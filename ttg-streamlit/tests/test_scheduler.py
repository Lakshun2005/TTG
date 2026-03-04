"""
Comprehensive scheduler tests — validates both CSP and GA solvers
can produce valid, conflict-free timetables under various scenarios.
"""
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
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _seed_base_data(db):
    """Seed a minimal valid dataset: 1 faculty, 1 subject, 1 room, 1 section, 4 timeslots."""
    fac = Faculty(name="Dr. Test", subject_specialization="Math", department="Science")
    db.add(fac)
    sub = Subject(name="Calculus", code="MAT101", credits=3, hours_per_week=2, semester=1, requires_lab=False)
    db.add(sub)
    room = Room(name="Room A", capacity=100, room_type="classroom")
    db.add(room)
    sec = Section(name="Sec A", semester=1, student_count=40)
    db.add(sec)
    for i, (day, period) in enumerate([
        ("Monday", 1), ("Monday", 2), ("Tuesday", 1), ("Tuesday", 2),
    ]):
        db.add(Timeslot(day_of_week=day, period_number=period,
                        start_time=datetime.time(9 + period - 1, 0),
                        end_time=datetime.time(10 + period - 1, 0)))
    db.commit()

    db.add(FacultySubject(faculty_id=fac.id, subject_id=sub.id))
    db.add(SectionSubject(section_id=sec.id, subject_id=sub.id, faculty_id=fac.id))
    db.commit()
    return fac, sub, room, sec


# ── CSP Solver Tests ──────────────────────────────────────────────────────


def test_csp_produces_valid_timetable(db):
    """CSP solver should produce a valid timetable with no conflicts."""
    _seed_base_data(db)
    gen = TimetableGeneration(status="pending")
    db.add(gen)
    db.commit()

    run_generation(db, gen.id, algorithm="csp")
    db.refresh(gen)

    assert gen.status == "success"
    entries = db.query(TimetableEntry).filter_by(generation_id=gen.id).all()
    assert len(entries) == 2  # hours_per_week=2


def test_csp_no_faculty_double_booking(db):
    """CSP: one faculty teaching 2 subjects should never be double-booked."""
    fac = Faculty(name="Prof. Busy", subject_specialization="CS", department="Eng")
    db.add(fac)
    sub1 = Subject(name="Algo", code="CS201", credits=3, hours_per_week=2, semester=1, requires_lab=False)
    sub2 = Subject(name="DS", code="CS202", credits=3, hours_per_week=2, semester=1, requires_lab=False)
    db.add_all([sub1, sub2])
    room = Room(name="R1", capacity=100, room_type="classroom")
    db.add(room)
    sec = Section(name="S1", semester=1, student_count=30)
    db.add(sec)
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday"]:
        for p in range(1, 3):
            db.add(Timeslot(day_of_week=day, period_number=p,
                            start_time=datetime.time(8 + p, 0),
                            end_time=datetime.time(9 + p, 0)))
    db.commit()

    db.add(FacultySubject(faculty_id=fac.id, subject_id=sub1.id))
    db.add(FacultySubject(faculty_id=fac.id, subject_id=sub2.id))
    db.add(SectionSubject(section_id=sec.id, subject_id=sub1.id, faculty_id=fac.id))
    db.add(SectionSubject(section_id=sec.id, subject_id=sub2.id, faculty_id=fac.id))
    db.commit()

    gen = TimetableGeneration(status="pending")
    db.add(gen)
    db.commit()
    run_generation(db, gen.id, algorithm="csp")
    db.refresh(gen)

    assert gen.status == "success"
    entries = db.query(TimetableEntry).filter_by(generation_id=gen.id).all()
    # No two entries should share (faculty_id, timeslot_id)
    fac_ts = [(e.faculty_id, e.timeslot_id) for e in entries]
    assert len(fac_ts) == len(set(fac_ts)), "Faculty double-booked!"


# ── GA Solver Tests ───────────────────────────────────────────────────────


def test_ga_produces_valid_timetable(db):
    """GA solver should produce a valid timetable with no conflicts."""
    _seed_base_data(db)
    gen = TimetableGeneration(status="pending")
    db.add(gen)
    db.commit()

    run_generation(db, gen.id, algorithm="ga")
    db.refresh(gen)

    assert gen.status == "success"
    entries = db.query(TimetableEntry).filter_by(generation_id=gen.id).all()
    assert len(entries) == 2


def test_ga_no_room_double_booking(db):
    """GA: two sections using 1 room should never share the same timeslot for that room."""
    fac1 = Faculty(name="F1", subject_specialization="Math", department="Sci")
    fac2 = Faculty(name="F2", subject_specialization="Phys", department="Sci")
    db.add_all([fac1, fac2])
    sub1 = Subject(name="Math", code="M1", credits=3, hours_per_week=1, semester=1, requires_lab=False)
    sub2 = Subject(name="Physics", code="P1", credits=3, hours_per_week=1, semester=1, requires_lab=False)
    db.add_all([sub1, sub2])
    room = Room(name="OnlyRoom", capacity=100, room_type="classroom")
    db.add(room)
    sec1 = Section(name="A", semester=1, student_count=30)
    sec2 = Section(name="B", semester=1, student_count=30)
    db.add_all([sec1, sec2])
    for day in ["Monday", "Tuesday"]:
        db.add(Timeslot(day_of_week=day, period_number=1,
                        start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)))
    db.commit()

    db.add(FacultySubject(faculty_id=fac1.id, subject_id=sub1.id))
    db.add(FacultySubject(faculty_id=fac2.id, subject_id=sub2.id))
    db.add(SectionSubject(section_id=sec1.id, subject_id=sub1.id, faculty_id=fac1.id))
    db.add(SectionSubject(section_id=sec2.id, subject_id=sub2.id, faculty_id=fac2.id))
    db.commit()

    gen = TimetableGeneration(status="pending")
    db.add(gen)
    db.commit()
    run_generation(db, gen.id, algorithm="ga")
    db.refresh(gen)

    assert gen.status == "success"
    entries = db.query(TimetableEntry).filter_by(generation_id=gen.id).all()
    room_ts = [(e.room_id, e.timeslot_id) for e in entries]
    assert len(room_ts) == len(set(room_ts)), "Room double-booked!"


# ── Edge Cases ────────────────────────────────────────────────────────────


def test_no_assignments_fails_gracefully(db):
    """Solver should report failure if no section-subject assignments exist."""
    db.add(Room(name="R1", capacity=50, room_type="classroom"))
    db.add(Timeslot(day_of_week="Monday", period_number=1,
                    start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)))
    db.commit()

    gen = TimetableGeneration(status="pending")
    db.add(gen)
    db.commit()
    run_generation(db, gen.id)
    db.refresh(gen)

    assert gen.status == "failed"
    assert "No section-subject assignments" in gen.error_message


def test_insufficient_rooms_fails(db):
    """If room capacity is too small, solver should fail gracefully."""
    fac = Faculty(name="F1", subject_specialization="CS", department="Eng")
    db.add(fac)
    sub = Subject(name="CS", code="CS1", credits=3, hours_per_week=1, semester=1, requires_lab=False)
    db.add(sub)
    # Room with capacity < student_count
    room = Room(name="TinyRoom", capacity=5, room_type="classroom")
    db.add(room)
    sec = Section(name="BigSection", semester=1, student_count=200)
    db.add(sec)
    db.add(Timeslot(day_of_week="Monday", period_number=1,
                    start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)))
    db.commit()

    db.add(FacultySubject(faculty_id=fac.id, subject_id=sub.id))
    db.add(SectionSubject(section_id=sec.id, subject_id=sub.id, faculty_id=fac.id))
    db.commit()

    gen = TimetableGeneration(status="pending")
    db.add(gen)
    db.commit()
    run_generation(db, gen.id)
    db.refresh(gen)

    assert gen.status == "failed"
    assert "No valid slots" in gen.error_message
