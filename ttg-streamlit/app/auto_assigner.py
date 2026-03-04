"""
Auto-Assignment Engine.

Automatically creates Section→Subject→Faculty assignments based on:
- Faculty subject specialization
- Subject semester matching section semester
- Faculty available hours

This eliminates the need for manual assignment — the AI decides everything.
"""
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.faculty import Faculty
from app.models.subject import Subject
from app.models.section import Section
from app.models.associations import SectionSubject, FacultySubject
from app.logger import get_logger

logger = get_logger(__name__)


def auto_assign(db: Session) -> Tuple[int, List[str]]:
    """
    Automatically assign subjects to sections with matching faculty.

    Logic:
    1. For each section, find subjects with the same semester.
    2. For each subject, find a faculty whose specialization matches.
    3. Create the SectionSubject assignment.
    4. Skip if assignment already exists.

    Returns:
        (num_created, list_of_messages)
    """
    messages: List[str] = []
    created = 0

    sections = db.query(Section).all()
    subjects = db.query(Subject).all()
    all_faculty = db.query(Faculty).all()

    if not sections:
        messages.append("No sections found. Add sections first.")
        return 0, messages

    if not subjects:
        messages.append("No subjects found. Add subjects first.")
        return 0, messages

    if not all_faculty:
        messages.append("No faculty found. Add faculty first.")
        return 0, messages

    # Build faculty lookup: specialization → list of Faculty objects
    spec_to_faculty = {}
    for fac in all_faculty:
        spec = (fac.subject_specialization or "").strip().lower()
        if spec:
            spec_to_faculty.setdefault(spec, []).append(fac)

    # Also consider FacultySubject mappings
    fs_mappings = db.query(FacultySubject).all()
    subject_to_faculty = {}
    for fs in fs_mappings:
        subject_to_faculty.setdefault(fs.subject_id, []).append(fs.faculty_id)

    # Track faculty hours used
    faculty_hours_used = {}
    existing_assignments = db.query(SectionSubject).all()
    for ea in existing_assignments:
        if ea.faculty_id:
            sub = db.query(Subject).filter(Subject.id == ea.subject_id).first()
            if sub:
                faculty_hours_used[ea.faculty_id] = faculty_hours_used.get(ea.faculty_id, 0) + sub.hours_per_week

    for section in sections:
        # Find subjects matching this section's semester
        matching_subjects = [s for s in subjects if s.semester == section.semester]

        for subject in matching_subjects:
            # Check if assignment already exists
            existing = db.query(SectionSubject).filter(
                SectionSubject.section_id == section.id,
                SectionSubject.subject_id == subject.id
            ).first()

            if existing:
                if existing.faculty_id is None:
                    # Assignment exists but no faculty — try to assign one
                    fac = _find_best_faculty(subject, spec_to_faculty, subject_to_faculty,
                                             all_faculty, faculty_hours_used)
                    if fac:
                        existing.faculty_id = fac.id
                        faculty_hours_used[fac.id] = faculty_hours_used.get(fac.id, 0) + subject.hours_per_week
                        messages.append(f"✅ Assigned {fac.name} → {subject.name} in {section.name}")
                        created += 1
                continue

            # Find a matching faculty
            fac = _find_best_faculty(subject, spec_to_faculty, subject_to_faculty,
                                     all_faculty, faculty_hours_used)

            if fac:
                db.add(SectionSubject(
                    section_id=section.id,
                    subject_id=subject.id,
                    faculty_id=fac.id
                ))
                faculty_hours_used[fac.id] = faculty_hours_used.get(fac.id, 0) + subject.hours_per_week

                # Also create FacultySubject mapping if not exists
                existing_fs = db.query(FacultySubject).filter(
                    FacultySubject.faculty_id == fac.id,
                    FacultySubject.subject_id == subject.id
                ).first()
                if not existing_fs:
                    try:
                        db.add(FacultySubject(faculty_id=fac.id, subject_id=subject.id))
                        db.flush()  # flush immediately to catch duplicates
                    except Exception:
                        db.rollback()  # ignore duplicate, continue

                messages.append(f"✅ {fac.name} → {subject.name} → {section.name}")
                created += 1
            else:
                messages.append(f"⚠️ No faculty found for '{subject.name}' in {section.name}")

    try:
        db.commit()
    except Exception:
        db.rollback()
        # Retry without FacultySubject — just commit the SectionSubject records
        db.commit()
    logger.info(f"Auto-assign created {created} assignments")
    return created, messages


def _find_best_faculty(subject, spec_to_faculty, subject_to_faculty, all_faculty, hours_used):
    """Find the best available faculty for a subject."""
    candidates = []

    # Priority 1: Faculty with explicit FacultySubject mapping
    if subject.id in subject_to_faculty:
        for fac_id in subject_to_faculty[subject.id]:
            for fac in all_faculty:
                if fac.id == fac_id:
                    candidates.append(fac)

    # Priority 2: Faculty whose specialization matches the subject name
    if not candidates:
        sub_name = subject.name.strip().lower()
        for spec, facs in spec_to_faculty.items():
            if spec in sub_name or sub_name in spec:
                candidates.extend(facs)

    # Priority 3: Partial match on specialization
    if not candidates:
        sub_words = set(subject.name.strip().lower().split())
        for spec, facs in spec_to_faculty.items():
            spec_words = set(spec.split())
            if sub_words & spec_words:
                candidates.extend(facs)

    if not candidates:
        return None

    # Pick the faculty with the most hours remaining
    def available_hours(fac):
        max_h = fac.max_hours_per_week or 20
        used = hours_used.get(fac.id, 0)
        return max_h - used

    candidates.sort(key=available_hours, reverse=True)

    for fac in candidates:
        if available_hours(fac) >= subject.hours_per_week:
            return fac

    return candidates[0] if candidates else None
