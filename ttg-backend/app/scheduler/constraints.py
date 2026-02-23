from typing import Dict, Tuple
from app.scheduler.domain_builder import Variable

Assignment = Dict[str, Tuple[int, int]]  # var_key -> (timeslot_id, room_id)


def is_consistent(var: Variable, value: Tuple[int, int], assignment: Assignment, all_vars: dict) -> bool:
    """Check all constraints for assigning value to var given current assignment."""
    timeslot_id, room_id = value

    for assigned_key, assigned_value in assignment.items():
        assigned_ts, assigned_room = assigned_value
        assigned_var = all_vars[assigned_key]

        if assigned_ts != timeslot_id:
            continue

        # Constraint 1: No faculty clash — same faculty cannot teach at same time
        if assigned_var.faculty_id == var.faculty_id:
            return False

        # Constraint 2: No section clash — same section cannot have two classes at same time
        if assigned_var.section_id == var.section_id:
            return False

        # Constraint 3: No room clash — same room cannot be used at same time
        if assigned_room == room_id:
            return False

    # Constraint 4: No duplicate slot per subject — same (section, subject) in same timeslot
    for assigned_key, assigned_value in assignment.items():
        assigned_ts, _ = assigned_value
        assigned_var = all_vars[assigned_key]
        if (assigned_var.section_id == var.section_id and
                assigned_var.subject_id == var.subject_id and
                assigned_ts == timeslot_id):
            return False

    return True
