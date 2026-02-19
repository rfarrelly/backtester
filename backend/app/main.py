from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base
from app.models import user

from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User

app = FastAPI()


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/test-user")
def create_test_user(db: Session = Depends(get_db)):
    user = User(email="test@example.com", password_hash="fakehash")
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": str(user.id), "email": user.email}
