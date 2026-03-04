"""Reset the database and seed fresh demo data."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import Base, get_engine, init_db, get_session
from app.models.faculty import Faculty
from app.models.subject import Subject
from app.models.room import Room
from app.models.section import Section
from app.models.timeslot import Timeslot
from app.models.associations import SectionSubject, FacultySubject
from app.models.timetable import TimetableGeneration, TimetableEntry
from app.crud.timeslot import crud_timeslot

# Completely reset the DB
engine = get_engine()
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("🗑️  Database reset")

db = get_session()
try:
    # ── Faculty (name, specialization, department) ──
    faculty_data = [
        ("Dr. Ramesh Kumar", "Mathematics", "Science"),
        ("Prof. Priya Sharma", "Computer Science", "Engineering"),
        ("Dr. Anand Verma", "Physics", "Science"),
        ("Prof. Meena Iyer", "English", "Humanities"),
        ("Dr. Suresh Nair", "Chemistry", "Science"),
    ]
    faculties = []
    for name, spec, dept in faculty_data:
        f = Faculty(name=name, subject_specialization=spec, department=dept, max_hours_per_week=20)
        db.add(f)
        faculties.append(f)
    db.commit()
    print(f"✅ {len(faculties)} faculty added")

    # ── Subjects ──
    subject_data = [
        ("Mathematics", "MAT101", 4, 4, 1, False),
        ("Computer Science", "CS201", 3, 3, 1, False),
        ("Physics", "PHY101", 3, 3, 1, False),
        ("English", "ENG101", 2, 2, 1, False),
        ("Chemistry", "CHE101", 3, 3, 1, False),
    ]
    subjects = []
    for name, code, credits, hpw, sem, lab in subject_data:
        s = Subject(name=name, code=code, credits=credits, hours_per_week=hpw, semester=sem, requires_lab=lab)
        db.add(s)
        subjects.append(s)
    db.commit()
    print(f"✅ {len(subjects)} subjects added")

    # ── Rooms ──
    room_data = [
        ("Room 101", 60, "classroom"),
        ("Room 102", 60, "classroom"),
        ("Room 103", 40, "classroom"),
    ]
    for name, cap, rtype in room_data:
        db.add(Room(name=name, capacity=cap, room_type=rtype))
    db.commit()
    print(f"✅ {len(room_data)} rooms added")

    # ── Sections ──
    sec_a = Section(name="Section A", semester=1, student_count=50)
    sec_b = Section(name="Section B", semester=1, student_count=45)
    db.add_all([sec_a, sec_b])
    db.commit()
    print("✅ 2 sections added")

    # ── Time Slots: 6 periods/day x 5 days = 30 slots ──
    crud_timeslot.bulk_generate(db, periods_per_day=6, start_hour=9, period_duration_minutes=60)
    print("✅ 30 time slots generated (Mon-Fri, 9AM-3PM)")

    print("\n🎉 Fresh demo data ready!")
    print("   Now go to ⚡ Generate Timetable and click Generate.")
    print("   The AI will auto-assign faculty→subjects→sections for you!")

finally:
    db.close()
