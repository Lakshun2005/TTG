import pytest
from app.scheduler.domain_builder import Variable
from app.scheduler.constraints import is_consistent

def test_no_double_booking_faculty():
    var1 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=0, requires_lab=False)
    var2 = Variable(section_id=2, subject_id=11, faculty_id=100, session_index=0, requires_lab=False)
    
    # Assign var1 to timeslot 1, room 5
    assignment = {var1.key(): (1, 5)}
    
    all_vars = {var1.key(): var1, var2.key(): var2}
    
    # Trying to assign var2 (same faculty) to timeslot 1 (even different room) should fail
    assert not is_consistent(var2, (1, 6), assignment, all_vars)
    # Trying to assign var2 to timeslot 2 should succeed
    assert is_consistent(var2, (2, 6), assignment, all_vars)

def test_no_double_booking_section():
    var1 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=0, requires_lab=False)
    var2 = Variable(section_id=1, subject_id=11, faculty_id=101, session_index=0, requires_lab=False)
    
    assignment = {var1.key(): (1, 5)}
    all_vars = {var1.key(): var1, var2.key(): var2}
    
    # Same section, different subject, different faculty. Timeslot 1 should fail.
    assert not is_consistent(var2, (1, 6), assignment, all_vars)
    # Timeslot 2 should succeed
    assert is_consistent(var2, (2, 6), assignment, all_vars)

def test_room_double_booking():
    var1 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=0, requires_lab=False)
    var2 = Variable(section_id=2, subject_id=11, faculty_id=101, session_index=0, requires_lab=False)
    
    assignment = {var1.key(): (1, 5)}
    all_vars = {var1.key(): var1, var2.key(): var2}
    
    # Same timeslot, same room should fail
    assert not is_consistent(var2, (1, 5), assignment, all_vars)
    # Same timeslot, different room should succeed
    assert is_consistent(var2, (1, 6), assignment, all_vars)
