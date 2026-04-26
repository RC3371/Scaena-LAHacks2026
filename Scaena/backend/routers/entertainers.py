from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models, schemas
from typing import List

router = APIRouter(prefix="/entertainers", tags=["entertainers"])


@router.get("/active", response_model=List[schemas.EntertainerOut])
def list_active(db: Session = Depends(get_db)):
    return db.query(models.Entertainer).filter(models.Entertainer.is_active == True).all()


@router.get("/{entertainer_id}", response_model=schemas.EntertainerOut)
def get_entertainer(entertainer_id: str, db: Session = Depends(get_db)):
    ent = db.query(models.Entertainer).filter(models.Entertainer.id == entertainer_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Entertainer not found")
    return ent


@router.post("", response_model=schemas.EntertainerOut)
def create_entertainer(data: schemas.EntertainerCreate, db: Session = Depends(get_db)):
    ent = models.Entertainer(**data.model_dump())
    db.add(ent)
    db.commit()
    db.refresh(ent)
    return ent


@router.put("/{entertainer_id}", response_model=schemas.EntertainerOut)
def update_entertainer(entertainer_id: str, data: schemas.EntertainerUpdate, db: Session = Depends(get_db)):
    ent = db.query(models.Entertainer).filter(models.Entertainer.id == entertainer_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Entertainer not found")
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(ent, key, val)
    db.commit()
    db.refresh(ent)
    return ent


@router.delete("/{entertainer_id}")
def deactivate_entertainer(entertainer_id: str, db: Session = Depends(get_db)):
    ent = db.query(models.Entertainer).filter(models.Entertainer.id == entertainer_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Entertainer not found")
    ent.is_active = False
    db.commit()
    return {"ok": True}
