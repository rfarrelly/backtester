# Backtester

A football betting backtesting platform for uploaded datasets.

## Features

- CSV dataset upload
- column mapping
- rule-based strategy simulation
- singles and multiples
- walk-forward validation
- custom calendar periods
- parameter sweeps
- persisted simulation runs
- run export

## Tech stack

- FastAPI
- React + TypeScript
- PostgreSQL
- Redis
- Docker Compose

## Local development

### 1. Create environment file

Create a `.env` file in the project root.

Example:

```env
APP_ENV=development
DEBUG=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/backtester
SECRET_KEY=dev_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:5173
```

### 2. Backend

uv sync

Run API

uv run uvicorn api.main:app --reload

### 3. Frontend

cd frontend
npm install
npm run dev

### 4. Run tests

uv run pytest -q

### 5. Docker

docker compose up --build
