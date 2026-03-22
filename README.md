# Backtester

A football betting backtesting platform built around uploaded datasets, rule-based strategies, calendar betting periods, and parameter sweeps.

The system is designed to be **model-agnostic** and **dataset-driven**, allowing users to test strategies based on their own features (e.g. edge, PPIDiff, etc.).

---

## ✨ Core Features

- 📁 Upload CSV datasets
- 🧭 Flexible column mapping
- ⚙️ Rule-based strategy engine
- 🎯 Singles and multiple-leg betting simulation
- 📅 Calendar-based betting (weekend/midweek/custom periods)
- 🔁 Walk-forward validation
- 📊 Parameter sweeps (grid search over rules)
- 💾 Persisted runs and reloadable configurations
- 📈 Equity curves and performance metrics
- 📤 Export bets/results to CSV

---

## 🧱 Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Celery (async tasks)
- Alembic (migrations)
- uv (dependency management)

### Frontend
- React
- TypeScript
- Vite

### Infrastructure
- Docker / Docker Compose
- GitHub Actions (CI)

---

## 🧠 Design Principles

- **Dataset-first**: all simulations operate on uploaded data
- **Rule-driven strategies**: no hardcoded betting logic
- **Model-agnostic**: edge and features come from user data
- **Reproducibility**: runs can be saved and reloaded
- **Extensibility**: new features should plug into rules and datasets

---

## 📁 Project Structure

```text
api/                  # FastAPI routes
app/
  application/        # Services (simulation, datasets, etc.)
  domain/             # Core logic (strategies, rules)
  infrastructure/     # DB, repositories, persistence models

frontend/
  src/                # React app

alembic/              # DB migrations

docker/               # Entrypoints, scripts
```

---

## ⚙️ Environment Setup

### 1. Create env file

```bash
cp .env.example .env.local
```

For Docker:

```bash
cp .env.example .env.docker
```

---

### Example `.env.local`

```env
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/backtester
SECRET_KEY=dev_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=60

CORS_ORIGINS=http://localhost:5173
```

---

### Example `.env.docker`

```env
APP_ENV=docker
DEBUG=true

DATABASE_URL=postgresql://postgres:postgres@postgres:5432/backtester
SECRET_KEY=dev_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=60

CORS_ORIGINS=http://localhost:5173

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=backtester
```

---

## 🚀 Running the App

## Option 1 — Docker (recommended)

```bash
docker compose up --build
```

### What happens automatically

The API container will:

1. wait for Postgres
2. run `alembic upgrade head`
3. start FastAPI

### Services

| Service   | URL                      |
|----------|--------------------------|
| API      | http://localhost:8000    |
| Frontend | http://localhost:5173    |
| Postgres | localhost:5432           |
| Redis    | localhost:6379           |

---

## Option 2 — Local (no Docker)

### Backend

```bash
uv sync
ENV_FILE=.env.local uv run alembic upgrade head
ENV_FILE=.env.local uv run uvicorn api.main:app --reload
```

---

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing

### Backend

```bash
uv run pytest -q
```

---

### Frontend

```bash
cd frontend
npm run build
```

---

## 🗄️ Database Migrations

### Create migration

```bash
uv run alembic revision --autogenerate -m "describe change"
```

### Apply migration

```bash
uv run alembic upgrade head
```

### Using Docker

```bash
docker compose exec api uv run alembic revision --autogenerate -m "describe change"
docker compose exec api uv run alembic upgrade head
```

---

## 🧠 Strategy System

Strategies are defined using:

- **Selection** → outcome to bet on (`H`, `D`, `A`)
- **Rule expression (optional)** → filter matches

### Example rules

```text
PPIDiff < 0.2
HomeTeamPPI < 1.0
AwayTeamPPI < 0.5
```

### Important

- The system does **not compute edge internally**
- If you want to use edge → include it in your dataset
- All features must exist as dataset columns

---

## 📅 Calendar Betting

Supports:

- Weekend vs midweek grouping
- Custom period definitions
- Ranking within periods
- Limiting number of bets per period

### Example use case

- Bet top 4 matches per weekend
- Ranked by `PPIDiff`
- Across all leagues

---

## 🔁 Parameter Sweeps

Allows testing multiple rule variations:

Example:

| Rule                     |
|--------------------------|
| PPIDiff < 0.1           |
| PPIDiff < 0.2           |
| PPIDiff < 0.4           |

Results include:

- ROI
- Profit
- Drawdown
- Strike rate
- Profit factor

---

## 💾 Saved Runs

- Simulation runs can be persisted
- Configurations can be reloaded into the UI
- Enables iterative experimentation

---

## 🔧 Development Workflow

### Backend

```bash
uv run pytest
```

### Frontend

```bash
cd frontend
npm run build
```

---

### When changing DB models

1. Update SQLAlchemy models
2. Generate migration
3. Review migration
4. Apply migration

---

## 🔁 CI Pipeline

GitHub Actions runs:

- backend tests
- database migrations
- frontend build

---

## ⚠️ Known Considerations

- `.venv` should not be mounted into Docker containers
- Always run migrations before API start (handled automatically in Docker)
- Custom SQLAlchemy types (e.g. JSON) may require manual fixes in migrations

---

## 🧭 Roadmap

### Near term
- Auth improvements (register/logout UX)
- UI/UX polish
- deployment setup (dev/staging/prod)

### Medium term
- strategy comparison mode
- richer sweep analytics
- custom period builder enhancements

### Long term
- cloud deployment (AWS/GCP)
- async simulation scaling
- experiment tracking

---

## 🤝 Contributing

See `CONTRIBUTING.md`.

---

## 📌 Summary

This project is built to:

- let users test **their own models**
- avoid hidden assumptions
- provide flexible, reproducible simulations
- support serious iterative strategy research

---

## License

TBD
