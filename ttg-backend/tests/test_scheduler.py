"""
Tests for the CSP scheduler engine.
Run with: pytest tests/test_scheduler.py -v
"""
import pytest
from app.scheduler.csp_solver import CSPSolver
from app.scheduler.domain_builder import Variable


def make_var(section_id, subject_id, faculty_id, session_index, requires_lab=False):
    return Variable(
        section_id=section_id,
        subject_id=subject_id,
        faculty_id=faculty_id,
        session_index=session_index,
        requires_lab=requires_lab
    )


def test_single_variable_solved():
    v = make_var(1, 1, 1, 0)
    domains = {v.key(): [(1, 1)]}
    solver = CSPSolver([v], domains)
    result = solver.solve()
    assert result is not None
    assert result[v.key()] == (1, 1)


def test_simple_two_vars_different_faculty():
    """Two classes, different faculty/sections — should trivially solve."""
    v1 = make_var(1, 1, 1, 0)
    v2 = make_var(2, 2, 2, 0)
    domains = {
        v1.key(): [(i, 1) for i in range(1, 11)],
        v2.key(): [(i, 1) for i in range(1, 11)],
    }
    solver = CSPSolver([v1, v2], domains)
    result = solver.solve()
    assert result is not None
    assert len(result) == 2


def test_faculty_clash_no_solution():
    """Same faculty, only one timeslot available — impossible."""
    v1 = make_var(1, 1, 1, 0)
    v2 = make_var(2, 2, 1, 0)  # same faculty_id=1
    domains = {
        v1.key(): [(1, 1)],
        v2.key(): [(1, 2)],  # Different room, same timeslot
    }
    solver = CSPSolver([v1, v2], domains)
    result = solver.solve()
    assert result is None


def test_section_clash_no_solution():
    """Same section, two classes forced into same timeslot — impossible."""
    v1 = make_var(1, 1, 1, 0)
    v2 = make_var(1, 2, 2, 0)  # same section_id=1, different faculty
    domains = {
        v1.key(): [(1, 1)],
        v2.key(): [(1, 2)],  # Same timeslot, different room — still a section clash
    }
    solver = CSPSolver([v1, v2], domains)
    result = solver.solve()
    assert result is None


def test_room_clash_no_solution():
    """Two classes same room same slot — impossible."""
    v1 = make_var(1, 1, 1, 0)
    v2 = make_var(2, 2, 2, 0)  # different section and faculty
    domains = {
        v1.key(): [(1, 1)],
        v2.key(): [(1, 1)],  # Same timeslot AND same room
    }
    solver = CSPSolver([v1, v2], domains)
    result = solver.solve()
    assert result is None


def test_multiple_sessions_distinct_timeslots():
    """Same subject/section/faculty needs 3 sessions, all in distinct timeslots."""
    vars_ = [make_var(1, 1, 1, i) for i in range(3)]
    domains = {v.key(): [(i, 1) for i in range(1, 8)] for v in vars_}
    solver = CSPSolver(vars_, domains)
    result = solver.solve()
    assert result is not None
    timeslots_used = [result[v.key()][0] for v in vars_]
    assert len(set(timeslots_used)) == 3  # All distinct


def test_empty_domain_no_solution():
    """A variable with an empty domain must immediately fail."""
    v = make_var(1, 1, 1, 0)
    domains = {v.key(): []}
    solver = CSPSolver([v], domains)
    result = solver.solve()
    assert result is None


def test_large_solvable_case():
    """
    Realistic scenario: 2 sections, 3 subjects each, 2 sessions/subject.
    12 variables total, 25 (timeslot, room) pairs per variable.
    Should find a solution.
    """
    variables = []
    for sec in range(1, 3):      # sections 1, 2
        for subj in range(1, 4):  # subjects 1, 2, 3
            for sess in range(2):  # 2 sessions each
                faculty_id = subj  # faculty matches subject
                variables.append(make_var(sec, subj, faculty_id, sess))

    # 5 timeslots × 5 rooms
    domain = [(ts, room) for ts in range(1, 26) for room in range(1, 6)]
    domains = {v.key(): list(domain) for v in variables}

    solver = CSPSolver(variables, domains)
    result = solver.solve()
    assert result is not None
    assert len(result) == len(variables)
