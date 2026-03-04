from typing import Dict, Tuple, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.scheduler.domain_builder import Variable, build_domains
from app.scheduler.csp_solver import CSPSolver
from app.models.timetable import TimetableGeneration, TimetableEntry
from app.logger import get_logger

logger = get_logger(__name__)

Assignment = Dict[str, Tuple[int, int]]


def persist_solution(db: Session, generation_id: str, variables: List[Variable], assignment: Assignment):
    var_map = {v.key(): v for v in variables}
    for var_key, (timeslot_id, room_id) in assignment.items():
        var = var_map[var_key]
        entry = TimetableEntry(
            section_id=var.section_id,
            subject_id=var.subject_id,
            faculty_id=var.faculty_id,
            room_id=room_id,
            timeslot_id=timeslot_id,
            generation_id=generation_id
        )
        db.add(entry)
    db.commit()
    logger.info(f"Persisted {len(assignment)} timetable entries for generation {generation_id[:8]}")


def run_generation(db: Session, generation_id: str, algorithm: str = "csp"):
    """Full pipeline: build domains → solve CSP/GA → persist or mark failed."""
    generation = db.query(TimetableGeneration).filter(
        TimetableGeneration.id == generation_id
    ).first()

    if not generation:
        logger.error(f"Generation {generation_id} not found")
        return

    try:
        generation.status = "running"
        db.commit()
        logger.info(f"Generation {generation_id[:8]} started (algorithm={algorithm})")

        variables, domains = build_domains(db)

        if not variables:
            generation.status = "failed"
            generation.error_message = (
                "No section-subject assignments found. "
                "Please assign subjects (with faculty) to sections first."
            )
            generation.completed_at = datetime.utcnow()
            db.commit()
            logger.warning(f"Generation {generation_id[:8]} failed: no variables")
            return

        for var in variables:
            if not domains.get(var.key()):
                generation.status = "failed"
                generation.error_message = (
                    f"No valid slots for subject_id={var.subject_id} in section_id={var.section_id}. "
                    "Check faculty specialization and ensure matching rooms exist."
                )
                generation.completed_at = datetime.utcnow()
                db.commit()
                logger.warning(f"Generation {generation_id[:8]} failed: empty domain for {var.key()}")
                return

        solution = None

        if algorithm == "ga":
            from app.scheduler.ga_solver import GeneticAlgorithmSolver
            solver = GeneticAlgorithmSolver(variables, domains)
            solution = solver.solve()
            logger.info(f"GA solver finished for generation {generation_id[:8]}")
        else:
            solver = CSPSolver(variables, domains)
            solution = solver.solve()
            logger.info(f"CSP solver finished for generation {generation_id[:8]}")

        if solution is None:
            generation.status = "failed"
            generation.error_message = (
                "No valid timetable found. Try: adding more rooms, "
                "reducing hours_per_week for subjects, or checking faculty specializations."
            )
        else:
            persist_solution(db, generation_id, variables, solution)
            generation.status = "success"

        generation.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"Generation {generation_id[:8]} exception: {e}", exc_info=True)
        generation = db.query(TimetableGeneration).filter(
            TimetableGeneration.id == generation_id
        ).first()
        if generation:
            generation.status = "failed"
            generation.error_message = str(e)
            generation.completed_at = datetime.utcnow()
            db.commit()
        raise
