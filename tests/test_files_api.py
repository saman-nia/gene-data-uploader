from pathlib import Path


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
