"""
Validation layer — checks data integrity before timetable generation.
Catches problems early and provides user-friendly error messages.
"""
from typing import Tuple, List
from collections import Counter
from sqlalchemy.orm import Session
from app.models.section import Section
from app.models.room import Room
from app.models.timeslot import Timeslot
from app.models.associations import SectionSubject
from app.logger import get_logger

logger = get_logger(__name__)


def validate_before_generation(db: Session) -> Tuple[bool, List[str]]:
    """
    Run all pre-generation validation checks.
    Returns (is_valid, list_of_error_messages).
    """
    errors: List[str] = []

    # 1. Must have sections
    sections = db.query(Section).all()
    if not sections:
        errors.append("No sections found. Add at least one section before generating.")

    # 2. Must have timeslots
    timeslot_count = db.query(Timeslot).count()
    if timeslot_count == 0:
        errors.append("No time slots found. Generate or add time slots first.")

    # 3. Must have rooms
    rooms = db.query(Room).all()
    if not rooms:
        errors.append("No rooms found. Add at least one room before generating.")

    # 4. Must have section-subject assignments
    assignments = db.query(SectionSubject).all()
    if not assignments:
        errors.append("No subject-faculty assignments found. Assign subjects to sections first.")
    else:
        # 4a. Check for assignments without faculty
        unassigned = [a for a in assignments if a.faculty_id is None]
        if unassigned:
            errors.append(
                f"{len(unassigned)} assignment(s) have no faculty assigned. "
                "Each subject in a section must have a faculty member."
            )

        # 4b. Check for duplicate assignments (same section + same subject)
        combos = [(a.section_id, a.subject_id) for a in assignments]
        counter = Counter(combos)
        dupes = {k: v for k, v in counter.items() if v > 1}
        if dupes:
            errors.append(
                f"Duplicate subject assignments detected in {len(dupes)} section(s). "
                "Remove duplicate assignments before generating."
            )

    # 5. Lab subjects need lab rooms
    if rooms and assignments:
        has_lab_rooms = any(r.room_type == "lab" for r in rooms)
        lab_assignments = []
        for a in assignments:
            if a.subject and a.subject.requires_lab:
                lab_assignments.append(a)

        if lab_assignments and not has_lab_rooms:
            errors.append(
                f"{len(lab_assignments)} subject(s) require a lab, but no lab rooms exist. "
                "Add at least one room of type 'lab'."
            )

    # 6. Sufficient timeslots for total hours needed
    if assignments and timeslot_count > 0:
        total_hours = sum(
            a.subject.hours_per_week for a in assignments
            if a.subject and a.faculty_id is not None
        )
        if total_hours > timeslot_count:
            errors.append(
                f"Total hours needed ({total_hours}) exceeds available time slots ({timeslot_count}). "
                "Add more time slots or reduce subject hours."
            )

    is_valid = len(errors) == 0
    if not is_valid:
        for e in errors:
            logger.warning(f"Validation: {e}")
    else:
        logger.info("Pre-generation validation passed")

    return is_valid, errors
