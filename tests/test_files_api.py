from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session as SqlAlchemySession


def upload_csv(client, filename: str, csv_bytes: bytes):
    return client.post(
        "/files/upload",
        files={"file": (filename, csv_bytes, "text/csv")},
    )


def test_end_to_end_upload_metadata_and_data(client):
    csv_bytes = (
        "gene_id;symbol;biotype\n"
        "ENSG000001;TP53;Protein Coding\n"
        "ENSG000002;BRCA1;Protein Coding\n"
    ).encode("utf-8")

    upload_response = upload_csv(client, "genes.csv", csv_bytes)

    assert upload_response.status_code == 201
    uploaded = upload_response.json()
    file_id = uploaded["id"]

    assert uploaded["column_count"] == 3
    assert uploaded["row_count"] == 2
    assert uploaded["delimiter"] == ";"

    metadata_response = client.get(f"/files/{file_id}/metadata")
    assert metadata_response.status_code == 200
    metadata = metadata_response.json()
    assert metadata["id"] == file_id
    assert metadata["original_filename"] == "genes.csv"

    data_response = client.get(f"/files/{file_id}/data")
    assert data_response.status_code == 200
    payload = data_response.json()

    assert payload["file_id"] == file_id
    assert payload["row_count"] == 2
    assert payload["returned_rows"] == 2
    assert payload["rows"][0]["symbol"] == "TP53"
    assert payload["rows"][1]["symbol"] == "BRCA1"


def test_list_files_returns_uploaded_items(client):
    csv_content = "a,b\n1,2\n".encode("utf-8")

    upload_response = upload_csv(client, "simple.csv", csv_content)
    assert upload_response.status_code == 201

    list_response = client.get("/files")
    assert list_response.status_code == 200

    payload = list_response.json()
    assert payload["total"] >= 1
    assert any(item["original_filename"] == "simple.csv" for item in payload["items"])


def test_upload_accepts_human_genes_dataset(client):
    dataset_path = Path(__file__).resolve().parents[1] / "data" / "genes_human.csv"
    assert dataset_path.exists(), "Expected genes_human.csv to exist in data/"

    with dataset_path.open("rb") as handle:
        response = client.post(
            "/files/upload",
            files={"file": ("genes_human.csv", handle, "text/csv")},
        )

    assert response.status_code == 201
    payload = response.json()

    assert payload["column_count"] == 7
    assert payload["row_count"] == 57992
    assert payload["delimiter"] == ";"

    data_response = client.get(f"/files/{payload['id']}/data", params={"limit": 2})
    assert data_response.status_code == 200

    data_payload = data_response.json()
    assert data_payload["returned_rows"] == 2
    assert set(data_payload["rows"][0].keys()) == set(payload["columns"])


def test_metadata_returns_404_for_unknown_file(client):
    response = client.get("/files/does-not-exist/metadata")
    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"


def test_data_returns_404_for_unknown_file(client):
    response = client.get("/files/does-not-exist/data")
    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"


def test_list_files_supports_filter_and_pagination(client):
    payload = "id,name\n1,A\n".encode("utf-8")
    assert upload_csv(client, "alpha.csv", payload).status_code == 201
    assert upload_csv(client, "beta.csv", payload).status_code == 201
    assert upload_csv(client, "alpha_extra.csv", payload).status_code == 201

    filtered_response = client.get("/files", params={"filename": "alpha"})
    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()

    assert filtered_payload["total"] == 2
    assert len(filtered_payload["items"]) == 2
    assert all("alpha" in item["original_filename"] for item in filtered_payload["items"])

    paged_response = client.get("/files", params={"offset": 1, "limit": 1})
    assert paged_response.status_code == 200
    paged_payload = paged_response.json()

    assert paged_payload["total"] == 3
    assert paged_payload["offset"] == 1
    assert paged_payload["limit"] == 1
    assert len(paged_payload["items"]) == 1


def test_upload_rejects_inconsistent_csv_and_cleans_storage(client, test_settings):
    invalid_csv = (
        "id;name\n"
        "1;A\n"
        "2\n"
    ).encode("utf-8")

    response = upload_csv(client, "invalid.csv", invalid_csv)
    assert response.status_code == 400
    assert "Invalid CSV file" in response.json()["detail"]
    assert list(test_settings.storage_root.glob("*")) == []

    files_response = client.get("/files")
    assert files_response.status_code == 200
    assert files_response.json()["total"] == 0


def test_upload_rejects_oversized_file_early_and_cleans_storage(client, test_settings):
    client.app.state.settings.max_upload_size_mb = 1

    oversized_csv = b"id,name\n" + (b"1,A\n" * 262144)

    response = upload_csv(client, "oversized.csv", oversized_csv)
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
    assert list(test_settings.storage_root.glob("*")) == []

    files_response = client.get("/files")
    assert files_response.status_code == 200
    assert files_response.json()["total"] == 0


def test_upload_cleans_file_if_metadata_commit_fails(client, test_settings, monkeypatch):
    def fail_commit(_self):
        raise SQLAlchemyError("simulated commit failure")

    monkeypatch.setattr(SqlAlchemySession, "commit", fail_commit)

    response = upload_csv(client, "commit_fail.csv", b"id,name\n1,A\n")
    assert response.status_code == 500
    assert response.json()["detail"] == "Unable to persist file metadata"
    assert list(test_settings.storage_root.glob("*")) == []

    files_response = client.get("/files")
    assert files_response.status_code == 200
    assert files_response.json()["total"] == 0


def test_upload_accepts_valid_csv_with_non_csv_extension(client):
    csv_bytes = "id,name\n1,A\n".encode("utf-8")
    response = upload_csv(client, "valid.txt", csv_bytes)

    assert response.status_code == 201
    payload = response.json()
    assert payload["column_count"] == 2
    assert payload["row_count"] == 1
