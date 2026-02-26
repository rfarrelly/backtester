from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_db
from app.ingestion.csv_loader import load_csv

router = APIRouter(tags=["data"])


@router.post("/load-data")
def load_data(db: Session = Depends(get_db)):
    load_csv("/app/app/data/sample.csv", db)
    return {"status": "loaded"}
