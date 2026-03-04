"""
Conflict detection tests — validates that the constraint checker
correctly identifies and rejects teacher, room, and section conflicts.
"""
import pytest
from app.scheduler.domain_builder import Variable
from app.scheduler.constraints import is_consistent


class TestTeacherConflicts:
    """Verify that the same teacher cannot teach two classes at once."""

    def test_same_faculty_same_timeslot_rejected(self):
        var1 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=0, requires_lab=False)
        var2 = Variable(section_id=2, subject_id=11, faculty_id=100, session_index=0, requires_lab=False)
        assignment = {var1.key(): (1, 5)}
        all_vars = {var1.key(): var1, var2.key(): var2}
        assert not is_consistent(var2, (1, 6), assignment, all_vars)

    def test_same_faculty_different_timeslot_accepted(self):
        var1 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=0, requires_lab=False)
        var2 = Variable(section_id=2, subject_id=11, faculty_id=100, session_index=0, requires_lab=False)
        assignment = {var1.key(): (1, 5)}
        all_vars = {var1.key(): var1, var2.key(): var2}
        assert is_consistent(var2, (2, 6), assignment, all_vars)

    def test_different_faculty_same_timeslot_accepted(self):
        var1 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=0, requires_lab=False)
        var2 = Variable(section_id=2, subject_id=11, faculty_id=101, session_index=0, requires_lab=False)
        assignment = {var1.key(): (1, 5)}
        all_vars = {var1.key(): var1, var2.key(): var2}
        assert is_consistent(var2, (1, 6), assignment, all_vars)


class TestRoomConflicts:
    """Verify that the same room cannot host two classes at the same time."""

    def test_same_room_same_timeslot_rejected(self):
        var1 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=0, requires_lab=False)
        var2 = Variable(section_id=2, subject_id=11, faculty_id=101, session_index=0, requires_lab=False)
        assignment = {var1.key(): (1, 5)}
        all_vars = {var1.key(): var1, var2.key(): var2}
        assert not is_consistent(var2, (1, 5), assignment, all_vars)

    def test_same_room_different_timeslot_accepted(self):
        var1 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=0, requires_lab=False)
        var2 = Variable(section_id=2, subject_id=11, faculty_id=101, session_index=0, requires_lab=False)
        assignment = {var1.key(): (1, 5)}
        all_vars = {var1.key(): var1, var2.key(): var2}
        assert is_consistent(var2, (2, 5), assignment, all_vars)


class TestSectionConflicts:
    """Verify that the same section cannot have two classes at the same time."""

    def test_same_section_same_timeslot_rejected(self):
        var1 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=0, requires_lab=False)
        var2 = Variable(section_id=1, subject_id=11, faculty_id=101, session_index=0, requires_lab=False)
        assignment = {var1.key(): (1, 5)}
        all_vars = {var1.key(): var1, var2.key(): var2}
        assert not is_consistent(var2, (1, 6), assignment, all_vars)

    def test_same_section_different_timeslot_accepted(self):
        var1 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=0, requires_lab=False)
        var2 = Variable(section_id=1, subject_id=11, faculty_id=101, session_index=0, requires_lab=False)
        assignment = {var1.key(): (1, 5)}
        all_vars = {var1.key(): var1, var2.key(): var2}
        assert is_consistent(var2, (2, 6), assignment, all_vars)


class TestDuplicateSubjectSlotConflicts:
    """Verify that the same subject for the same section is not placed twice at the same time."""

    def test_duplicate_subject_same_section_same_timeslot_rejected(self):
        var1 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=0, requires_lab=False)
        var2 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=1, requires_lab=False)
        assignment = {var1.key(): (1, 5)}
        all_vars = {var1.key(): var1, var2.key(): var2}
        # Same section + same faculty + same timeslot → rejected
        assert not is_consistent(var2, (1, 5), assignment, all_vars)


class TestMultipleConflicts:
    """Verify correctness with multiple assignments already in place."""

    def test_no_conflict_in_full_assignment(self):
        var1 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=0, requires_lab=False)
        var2 = Variable(section_id=2, subject_id=11, faculty_id=101, session_index=0, requires_lab=False)
        var3 = Variable(section_id=3, subject_id=12, faculty_id=102, session_index=0, requires_lab=False)
        assignment = {var1.key(): (1, 5), var2.key(): (2, 6)}
        all_vars = {var1.key(): var1, var2.key(): var2, var3.key(): var3}
        # var3 has unique section/faculty/room/timeslot
        assert is_consistent(var3, (3, 7), assignment, all_vars)

    def test_conflict_with_second_assignment(self):
        var1 = Variable(section_id=1, subject_id=10, faculty_id=100, session_index=0, requires_lab=False)
        var2 = Variable(section_id=2, subject_id=11, faculty_id=101, session_index=0, requires_lab=False)
        var3 = Variable(section_id=3, subject_id=12, faculty_id=101, session_index=0, requires_lab=False)
        assignment = {var1.key(): (1, 5), var2.key(): (2, 6)}
        all_vars = {var1.key(): var1, var2.key(): var2, var3.key(): var3}
        # var3 conflicts with var2 (same faculty, same timeslot)
        assert not is_consistent(var3, (2, 7), assignment, all_vars)
