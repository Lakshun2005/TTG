from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
import app.models  # noqa: F401 — registers all models with Base
from app.routers import faculty, subjects, rooms, sections, timeslots, timetable, export

# Auto-create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TTG — Time Table Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(faculty.router)
app.include_router(subjects.router)
app.include_router(rooms.router)
app.include_router(sections.router)
app.include_router(timeslots.router)
app.include_router(timetable.router)
app.include_router(export.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "TTG Backend"}
