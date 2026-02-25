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
    blocks = db.query(FacultyAvailability).all()
    faculty_blocked: Dict[int, set] = {}
    for b in blocks:
        if b.faculty_id not in faculty_blocked:
            faculty_blocked[b.faculty_id] = set()
        faculty_blocked[b.faculty_id].add(b.timeslot_id)

    all_timeslots = db.query(Timeslot).all()
    all_rooms = db.query(Room).all()
    classrooms = [r for r in all_rooms if r.room_type == "classroom"]
    labs = [r for r in all_rooms if r.room_type == "lab"]

    assignments = db.query(SectionSubject).all()
    variables = []
    domains = {}

    for ss in assignments:
        if ss.faculty_id is None:
            continue
        subject = ss.subject
        faculty_id = ss.faculty_id
        hours = subject.hours_per_week
        blocked = faculty_blocked.get(faculty_id, set())
        available_timeslots = [ts for ts in all_timeslots if ts.id not in blocked]
        valid_rooms = labs if subject.requires_lab else classrooms
        domain = [(ts.id, r.id) for ts in available_timeslots for r in valid_rooms]

        for session_idx in range(hours):
            var = Variable(
                section_id=ss.section_id,
                subject_id=subject.id,
                faculty_id=faculty_id,
                session_index=session_idx,
                requires_lab=subject.requires_lab,
            )
            variables.append(var)
            domains[var.key()] = list(domain)

    return variables, domains
