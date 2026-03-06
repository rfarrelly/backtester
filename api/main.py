from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.infrastructure.db.models  # noqa: F401
from api.routes import auth, data, datasets, rules, runs, simulation, users
from app.infrastructure.db.base import Base
from app.infrastructure.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok"}


app.include_router(rules.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(simulation.router)
app.include_router(data.router)
app.include_router(datasets.router)
app.include_router(runs.router)
