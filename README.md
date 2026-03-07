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

## Sample dataset

The `data/genes_human.csv` file is **not included** in the repository for data privacy reasons. To run the full test suite or try the Swagger example below, download it manually:

1. Get `genes_human.csv` from [HGNC](https://www.genenames.org/download/statistics-and-files/) (use the "Complete dataset" download, semicolon-delimited)
2. Place it at `data/genes_human.csv`

Without this file the real-dataset test will be skipped automatically.

## How to test it with Swagger

Open [http://localhost:8000/docs](http://localhost:8000/docs) and try the following:

### Step 1 — Upload a CSV file

1. Expand **POST /files/upload**
2. Click **Try it out**
3. Choose a CSV file (e.g. `data/genes_human.csv` if you downloaded it, or any other CSV)
4. Click **Execute**
5. Copy the `id` from the response — you need it for the next steps

### Step 2 — List uploaded files

1. Expand **GET /files**
2. Click **Try it out**, then **Execute**
3. You can filter by `filename` or use `offset` and `limit` for pagination

### Step 3 — Get file metadata

1. Expand **GET /files/{file_id}/metadata**
2. Paste the `id` from Step 1
3. Click **Execute**

### Step 4 — Get CSV data as JSON

1. Expand **GET /files/{file_id}/data**
2. Paste the `id` from Step 1
3. You can set `offset` and `limit` to paginate through large files. By default, the `limit` is 100.
4. Click **Execute**

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

What is covered:

- CSV parsing (delimiter detection, row validation)
- Full flow: upload → metadata → data retrieval
- Real dataset test with `data/genes_human.csv` (skipped if file is not present)
- Error cases: invalid CSV, oversized files, DB failures, 404s

## Local development (without Docker)

If you want to run the API locally:

```bash
poetry install
docker compose up db -d          # start only PostgreSQL
cp .env.example .env             # configure environment variables
poetry run uvicorn gene_data_uploader.main:app --reload --host 0.0.0.0 --port 8000
```

## Project structure

```
gene-data-uploader/
│
├── src/gene_data_uploader/
│   ├── main.py                    # Uvicorn entrypoint
│   ├── app.py                     # Application factory
│   │
│   ├── core/
│   │   └── config.py              # Settings (pydantic-settings)
│   │
│   ├── db/
│   │   ├── base.py                # SQLAlchemy DeclarativeBase
│   │   ├── models.py              # SQLAlchemy model (UploadedFile)
│   │   └── session.py             # Engine and session factory
│   │
│   ├── schemas/
│   │   └── file.py                # Pydantic response schemas
│   │
│   ├── services/
│   │   └── csv_utils.py           # CSV parsing and validation
│   │
│   ├── storage/
│   │   ├── base.py                # Abstract storage interface
│   │   ├── local.py               # Local filesystem storage
│   │   └── factory.py             # Storage backend factory
│   │
│   └── api/routes/
│       └── files.py               # API route handlers
│
├── tests/                         # Test suite (pytest + SQLite)
├── data/                          # Sample datasets
│
├── Dockerfile                     # Container image definition
├── docker-compose.yml             # Multi-container orchestration
├── pyproject.toml                 # Dependencies (Poetry)
├── Makefile                       # Dev commands (run, test, docker)
└── .env.example                   # Environment variable template
```

## Design decisions

- **Storage abstraction** — File storage uses an abstract interface (`AbstractStorage`), so it is easy to switch from local disk to something like S3 or MinIO later.
- **Streaming uploads** — Files are written in chunks, so large files don't load fully into memory.
- **Cleanup on failure** — If validation or the database commit fails, the stored file gets deleted automatically.
- **SQLite for tests** — Tests use SQLite instead of PostgreSQL, so no extra setup is needed to run them.
