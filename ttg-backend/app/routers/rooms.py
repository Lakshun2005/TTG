from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.room import crud_room
from app.schemas.room import RoomRead, RoomCreate, RoomUpdate

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=List[RoomRead])
def get_rooms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_room.get_all(db, skip=skip, limit=limit)


@router.post("", response_model=RoomRead)
def create_room(data: RoomCreate, db: Session = Depends(get_db)):
    return crud_room.create(db, data)


@router.get("/{room_id}", response_model=RoomRead)
def get_room(room_id: int, db: Session = Depends(get_db)):
    obj = crud_room.get(db, room_id)
    if not obj:
        raise HTTPException(404, "Room not found")
    return obj


@router.put("/{room_id}", response_model=RoomRead)
def update_room(room_id: int, data: RoomUpdate, db: Session = Depends(get_db)):
    obj = crud_room.get(db, room_id)
    if not obj:
        raise HTTPException(404, "Room not found")
    return crud_room.update(db, obj, data)


@router.delete("/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db)):
    obj = crud_room.delete(db, room_id)
    if not obj:
        raise HTTPException(404, "Room not found")
    return {"ok": True}
