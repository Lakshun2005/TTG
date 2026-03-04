from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import Base
from app.logger import get_logger

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 200) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, data: dict) -> ModelType:
        try:
            db_obj = self.model(**data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created {self.model.__name__} id={db_obj.id}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create {self.model.__name__}: {e}", exc_info=True)
            raise

    def update(self, db: Session, id: int, data: dict) -> Optional[ModelType]:
        try:
            db_obj = self.get(db, id)
            if db_obj:
                for field, value in data.items():
                    setattr(db_obj, field, value)
                db.commit()
                db.refresh(db_obj)
                logger.info(f"Updated {self.model.__name__} id={id}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update {self.model.__name__} id={id}: {e}", exc_info=True)
            raise

    def delete(self, db: Session, id: int) -> Optional[ModelType]:
        try:
            obj = db.get(self.model, id)
            if obj:
                db.delete(obj)
                db.commit()
                logger.info(f"Deleted {self.model.__name__} id={id}")
            return obj
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete {self.model.__name__} id={id}: {e}", exc_info=True)
            raise
