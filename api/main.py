from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import auth, data, simulation, users
from app.infrastructure.db.base import Base
from app.infrastructure.db.session import engine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
