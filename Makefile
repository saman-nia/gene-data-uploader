.PHONY: install run test docker-up docker-down

install:
	poetry install

run:
	poetry run uvicorn gene_data_uploader.main:app --reload --host 0.0.0.0 --port 8000

test:
	poetry run pytest

docker-up:
	docker compose up --build

docker-down:
	docker compose down -v
