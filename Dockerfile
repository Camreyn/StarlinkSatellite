FROM python:3.11-slim AS api

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend
COPY backend/pyproject.toml ./pyproject.toml
COPY backend/app ./app
COPY backend/scripts ./scripts
RUN pip install --no-cache-dir -e .

WORKDIR /app
COPY sample_data ./sample_data
WORKDIR /app/backend

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
