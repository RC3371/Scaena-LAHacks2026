from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models, schemas
from typing import List
import json

router = APIRouter(prefix="/venues", tags=["venues"])


@router.post("/bulk")
def bulk_upsert_venues(data: schemas.VenueBulkCreate, db: Session = Depends(get_db)):
    created = 0
    for v in data.venues:
        venue = models.Venue(
            entertainer_id=data.entertainer_id,
            name=v.get("name"),
            contact_name=v.get("contact_name"),
            contact_email=v.get("contact_email"),
            source_url=v.get("source_url"),
            venue_type=v.get("venue_type") or v.get("name"),
            typical_pay=v.get("typical_pay"),
            fit_score=v.get("fit_score"),
            contact_approach=v.get("contact_approach"),
            why_fits=v.get("why_fits"),
            specific_examples=json.dumps(v.get("specific_examples", [])),
        )
        db.add(venue)
        created += 1
    db.commit()
    return {"created": created}


@router.get("/{entertainer_id}", response_model=List[schemas.VenueOut])
def list_venues(entertainer_id: str, db: Session = Depends(get_db)):
    return db.query(models.Venue).filter(models.Venue.entertainer_id == entertainer_id).all()
