from datetime import time
from typing import List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.timeslot import Timeslot
from app.schemas.timeslot import TimeslotCreate, TimeslotUpdate

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


class CRUDTimeslot(CRUDBase[Timeslot, TimeslotCreate, TimeslotUpdate]):
    def bulk_generate(self, db: Session, periods_per_day: int, start_hour: int, period_duration_minutes: int) -> List[Timeslot]:
        # Clear existing timeslots
        db.query(Timeslot).delete()
        db.commit()

        for day in DAYS:
            start_minutes = start_hour * 60
            for period in range(1, periods_per_day + 1):
                end_minutes = start_minutes + period_duration_minutes
                start_t = time(start_minutes // 60, start_minutes % 60)
                end_t = time(end_minutes // 60, end_minutes % 60)
                ts = Timeslot(
                    day_of_week=day,
                    period_number=period,
                    start_time=start_t,
                    end_time=end_t
                )
                db.add(ts)
                start_minutes = end_minutes
            db.commit()

        return db.query(Timeslot).order_by(Timeslot.day_of_week, Timeslot.period_number).all()


crud_timeslot = CRUDTimeslot(Timeslot)
