"""
Input validation tests — verifies that the validation layer
catches bad data before it reaches the scheduler.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.subject import Subject
from app.models.faculty import Faculty
from app.models.room import Room
from app.models.section import Section
from app.models.timeslot import Timeslot
from app.models.associations import SectionSubject, FacultySubject
from app.validator import validate_before_generation

import datetime

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


def test_empty_database_fails(db):
    """Nothing in DB → validation should fail."""
    ok, errors = validate_before_generation(db)
    assert not ok
    assert any("No sections" in e for e in errors)


def test_no_timeslots_fails(db):
    """Sections exist but no timeslots → fail."""
    db.add(Section(name="S1", semester=1, student_count=30))
    db.commit()
    ok, errors = validate_before_generation(db)
    assert not ok
    assert any("No time slots" in e for e in errors)


def test_no_rooms_fails(db):
    """Sections + timeslots but no rooms → fail."""
    db.add(Section(name="S1", semester=1, student_count=30))
    db.add(Timeslot(day_of_week="Monday", period_number=1,
                    start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)))
    db.commit()
    ok, errors = validate_before_generation(db)
    assert not ok
    assert any("No rooms" in e for e in errors)


def test_no_assignments_fails(db):
    """Everything exists but subjects aren't assigned to sections → fail."""
    db.add(Section(name="S1", semester=1, student_count=30))
    db.add(Room(name="R1", capacity=50, room_type="classroom"))
    db.add(Timeslot(day_of_week="Monday", period_number=1,
                    start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)))
    db.commit()
    ok, errors = validate_before_generation(db)
    assert not ok
    assert any("No subject-faculty assignments" in e for e in errors)


def test_assignment_without_faculty_warns(db):
    """Assignment exists but faculty_id is None → should warn."""
    fac = Faculty(name="F1", subject_specialization="Math", department="Sci")
    sub = Subject(name="Math", code="M1", credits=3, hours_per_week=1, semester=1, requires_lab=False)
    db.add_all([fac, sub])
    sec = Section(name="S1", semester=1, student_count=30)
    db.add(sec)
    db.add(Room(name="R1", capacity=50, room_type="classroom"))
    db.add(Timeslot(day_of_week="Monday", period_number=1,
                    start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)))
    db.commit()

    # Assignment WITHOUT a faculty
    db.add(SectionSubject(section_id=sec.id, subject_id=sub.id, faculty_id=None))
    db.commit()

    ok, errors = validate_before_generation(db)
    assert not ok
    assert any("no faculty assigned" in e.lower() for e in errors)


def test_valid_data_passes(db):
    """Fully valid data should pass validation."""
    fac = Faculty(name="F1", subject_specialization="Math", department="Sci")
    sub = Subject(name="Math", code="M1", credits=3, hours_per_week=1, semester=1, requires_lab=False)
    db.add_all([fac, sub])
    room = Room(name="R1", capacity=50, room_type="classroom")
    db.add(room)
    sec = Section(name="S1", semester=1, student_count=30)
    db.add(sec)
    db.add(Timeslot(day_of_week="Monday", period_number=1,
                    start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)))
    db.commit()

    db.add(FacultySubject(faculty_id=fac.id, subject_id=sub.id))
    db.add(SectionSubject(section_id=sec.id, subject_id=sub.id, faculty_id=fac.id))
    db.commit()

    ok, errors = validate_before_generation(db)
    assert ok
    assert len(errors) == 0


def test_lab_subject_without_lab_room_fails(db):
    """Lab subject but only classroom rooms → should fail."""
    fac = Faculty(name="F1", subject_specialization="Chem", department="Sci")
    sub = Subject(name="Chem Lab", code="CH1", credits=2, hours_per_week=1, semester=1, requires_lab=True)
    db.add_all([fac, sub])
    room = Room(name="R1", capacity=50, room_type="classroom")  # NOT a lab
    db.add(room)
    sec = Section(name="S1", semester=1, student_count=30)
    db.add(sec)
    db.add(Timeslot(day_of_week="Monday", period_number=1,
                    start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)))
    db.commit()

    db.add(FacultySubject(faculty_id=fac.id, subject_id=sub.id))
    db.add(SectionSubject(section_id=sec.id, subject_id=sub.id, faculty_id=fac.id))
    db.commit()

    ok, errors = validate_before_generation(db)
    assert not ok
    assert any("lab" in e.lower() for e in errors)


def test_duplicate_section_subject_rejected_by_db(db):
    """Same subject assigned twice to same section should be rejected by DB constraint."""
    from sqlalchemy.exc import IntegrityError as SAIntegrityError

    fac = Faculty(name="F1", subject_specialization="Math", department="Sci")
    sub = Subject(name="Math", code="M1", credits=3, hours_per_week=1, semester=1, requires_lab=False)
    db.add_all([fac, sub])
    room = Room(name="R1", capacity=50, room_type="classroom")
    db.add(room)
    sec = Section(name="S1", semester=1, student_count=30)
    db.add(sec)
    db.add(Timeslot(day_of_week="Monday", period_number=1,
                    start_time=datetime.time(9, 0), end_time=datetime.time(10, 0)))
    db.commit()

    db.add(FacultySubject(faculty_id=fac.id, subject_id=sub.id))
    db.add(SectionSubject(section_id=sec.id, subject_id=sub.id, faculty_id=fac.id))
    db.commit()

    # The DB UNIQUE constraint on (section_id, subject_id) prevents duplicates at the DB level
    db.add(SectionSubject(section_id=sec.id, subject_id=sub.id, faculty_id=fac.id))
    with pytest.raises(SAIntegrityError):
        db.commit()
