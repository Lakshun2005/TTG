from dataclasses import dataclass
from typing import List, Tuple, Dict
from sqlalchemy.orm import Session
from app.models.associations import SectionSubject, FacultyAvailability
from app.models.room import Room
from app.models.timeslot import Timeslot


@dataclass
class Variable:
    section_id: int
    subject_id: int
    faculty_id: int
    session_index: int
    requires_lab: bool

    def key(self) -> str:
        return f"{self.section_id}_{self.subject_id}_{self.faculty_id}_{self.session_index}"


def build_domains(db: Session) -> Tuple[List[Variable], Dict[str, List[Tuple[int, int]]]]:
    """
    Returns (variables, domains) where:
    - variables: list of Variable objects (one per class session)
    - domains: dict mapping variable.key() -> list of (timeslot_id, room_id) pairs
    """
    # Get all blocked timeslots per faculty
    blocks = db.query(FacultyAvailability).all()
    faculty_blocked: Dict[int, set] = {}
    for b in blocks:
        if b.faculty_id not in faculty_blocked:
            faculty_blocked[b.faculty_id] = set()
        faculty_blocked[b.faculty_id].add(b.timeslot_id)

    # Get all timeslots
    all_timeslots = db.query(Timeslot).all()

    # Get all rooms
    all_rooms = db.query(Room).all()
    classrooms = [r for r in all_rooms if r.room_type == "classroom"]
    labs = [r for r in all_rooms if r.room_type == "lab"]

    # Get all section-subject assignments (only those with a faculty assigned)
    assignments = db.query(SectionSubject).all()

    variables = []
    domains = {}

    for ss in assignments:
        if ss.faculty_id is None:
            continue  # Skip unassigned subjects

        subject = ss.subject
        faculty_id = ss.faculty_id
        hours = subject.hours_per_week

        # Determine available timeslots for this faculty
        blocked = faculty_blocked.get(faculty_id, set())
        available_timeslots = [ts for ts in all_timeslots if ts.id not in blocked]

        # Determine valid rooms
        valid_rooms = labs if subject.requires_lab else classrooms

        # Build domain: all (timeslot_id, room_id) combinations
        domain = [(ts.id, r.id) for ts in available_timeslots for r in valid_rooms]

        for session_idx in range(hours):
            var = Variable(
                section_id=ss.section_id,
                subject_id=subject.id,
                faculty_id=faculty_id,
                session_index=session_idx,
                requires_lab=subject.requires_lab
            )
            variables.append(var)
            domains[var.key()] = list(domain)

    return variables, domains
