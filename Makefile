.PHONY: install backend frontend test lint format init-db ingest-starlink ingest-satcat docker-up docker-down

install:
	cd backend && python -m pip install -e ".[dev]"
	cd frontend && npm install

backend:
	cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest
	cd frontend && npm test

lint:
	cd backend && ruff check app tests && mypy app
	cd frontend && npm run lint

format:
	cd backend && ruff format app tests
	cd frontend && npm run format

init-db:
	cd backend && python scripts/init_db.py

ingest-starlink:
	curl -X POST http://localhost:8000/api/ingest/celestrak/starlink

ingest-satcat:
	curl -X POST http://localhost:8000/api/ingest/celestrak/satcat

docker-up:
	docker compose up --build

docker-down:
	docker compose down
