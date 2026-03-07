# Gene Data Uploader

A REST API for uploading CSV files and getting the data back as JSON. Built with **FastAPI** and **PostgreSQL**.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)

## Getting started

**1. Clone and run:**

```bash
git clone https://github.com/saman-nia/gene-data-uploader.git
cd gene-data-uploader
docker compose up --build
```

Wait until you see `Uvicorn running on http://0.0.0.0:8000`. This starts both the API and a PostgreSQL database. Tables are created automatically on first run.

**2. Open Swagger UI:**

Go to [http://localhost:8000/docs](http://localhost:8000/docs) — you can test all endpoints from there.

**3. Stop everything:**

```bash
docker compose down -v
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/files/upload` | Upload a CSV file |
| `GET` | `/files` | List files (supports `offset`, `limit`, `filename`) |
| `GET` | `/files/{file_id}/metadata` | Get metadata for one file |
| `GET` | `/files/{file_id}/data` | Get CSV content as JSON (supports `offset`, `limit`) |
| `GET` | `/health` | Health check |

## Running tests

Tests run with SQLite so you don't need PostgreSQL:

```bash
poetry install
poetry run pytest
```

## Local development (without Docker)

If you want to run the API locally:

```bash
poetry install
docker compose up db -d          # start only PostgreSQL
cp .env.example .env             # configure environment variables
poetry run uvicorn gene_data_uploader.main:app --reload --host 0.0.0.0 --port 8000
```
