.PHONY: dev install lint test migrate docker-up docker-down

install:
	pip install -r requirements.txt

dev:
	uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check src/ --fix
	ruff format src/

test:
	pytest tests/ -v

docker-up:
	docker compose up -d

docker-down:
	docker compose down
