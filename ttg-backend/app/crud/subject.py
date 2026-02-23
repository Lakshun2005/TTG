from app.crud.base import CRUDBase
from app.models.subject import Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate


class CRUDSubject(CRUDBase[Subject, SubjectCreate, SubjectUpdate]):
    pass


crud_subject = CRUDSubject(Subject)
