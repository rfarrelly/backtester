FROM python:3.11-slim

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN pip install --upgrade pip
RUN pip install uv
RUN uv sync --frozen

COPY . .

CMD ["uv", "run", "celery", "-A", "worker.tasks", "worker", "--loglevel=info"]