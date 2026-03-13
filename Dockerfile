FROM mirror.gcr.io/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN pip install --no-cache-dir poetry==1.8.3

COPY pyproject.toml README.md ./
RUN poetry install --without dev --no-root

COPY src ./src
COPY data ./data

EXPOSE 8000

CMD ["uvicorn", "gene_data_uploader.main:app", "--host", "0.0.0.0", "--port", "8000"]
