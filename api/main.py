from fastapi import FastAPI

from api.routes import auth, data, simulation, users
from app.db.base import Base
from app.db.session import engine

app = FastAPI()


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def health_check():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(simulation.router)
app.include_router(data.router)
