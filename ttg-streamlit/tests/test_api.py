import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.crud.faculty import crud_faculty
from app.crud.base import CRUDBase
from app.models.subject import Subject

# Test DB in-memory
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
crud_subject = CRUDBase(Subject)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_faculty_crud(db):
    # Create
    fac = crud_faculty.create(db, {
        "name": "Dr. Smith", 
        "subject_specialization": "Computer Science", 
        "department": "Engineering", 
        "max_hours_per_week": 15
    })
    assert fac.id is not None
    assert fac.subject_specialization == "Computer Science"
    
    # Read
    fetched = crud_faculty.get(db, fac.id)
    assert fetched.name == "Dr. Smith"
    
    # Update
    crud_faculty.update(db, fac.id, {"subject_specialization": "AI"})
    updated = crud_faculty.get(db, fac.id)
    assert updated.subject_specialization == "AI"
    
    # Delete
    crud_faculty.delete(db, fac.id)
    assert crud_faculty.get(db, fac.id) is None

def test_subject_crud(db):
    sub = crud_subject.create(db, {
        "name": "Algorithms", "code": "CS101", "credits": 3,
        "hours_per_week": 3, "semester": 1, "requires_lab": False
    })
    assert sub.id is not None
    
    fetched = crud_subject.get(db, sub.id)
    assert fetched.code == "CS101"
    
    crud_subject.update(db, sub.id, {"code": "CS102"})
    assert crud_subject.get(db, sub.id).code == "CS102"
    
    crud_subject.delete(db, sub.id)
    assert crud_subject.get(db, sub.id) is None
