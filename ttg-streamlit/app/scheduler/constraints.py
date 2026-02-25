from typing import Dict, Tuple
from app.scheduler.domain_builder import Variable

Assignment = Dict[str, Tuple[int, int]]


def is_consistent(var: Variable, value: Tuple[int, int], assignment: Assignment, all_vars: dict) -> bool:
    timeslot_id, room_id = value

    for assigned_key, assigned_value in assignment.items():
        assigned_ts, assigned_room = assigned_value
        assigned_var = all_vars[assigned_key]

        if assigned_ts != timeslot_id:
            continue

        if assigned_var.faculty_id == var.faculty_id:
            return False
        if assigned_var.section_id == var.section_id:
            return False
        if assigned_room == room_id:
            return False

    for assigned_key, assigned_value in assignment.items():
        assigned_ts, _ = assigned_value
        assigned_var = all_vars[assigned_key]
        if (assigned_var.section_id == var.section_id and
                assigned_var.subject_id == var.subject_id and
                assigned_ts == timeslot_id):
            return False

    return True
