from pathlib import Path

from app.api.routes import documents as documents_route


class StubSettings:
    raw_data_dir = ""
    upload_dir = ""
    qdrant_collection = "knowledge_base"
    openai_api_key = ""


class StubVectorStore:
    def __init__(self, indexed_documents: list[dict]) -> None:
        self._indexed_documents = indexed_documents

    def ping(self) -> bool:
        return True

    def collection_exists(self) -> bool:
        return True

    def count_points(self) -> int:
        return 3

    def list_indexed_documents(self) -> list[dict]:
        return self._indexed_documents

    def delete_by_file_path(self, _: str) -> int:
        return 0


def test_build_document_inventory_marks_pending_and_orphaned(tmp_path, monkeypatch) -> None:
    raw_dir = tmp_path / "raw"
    upload_dir = tmp_path / "uploads"
    raw_dir.mkdir()
    upload_dir.mkdir()

    disk_file = raw_dir / "notes.md"
    disk_file.write_text("hello", encoding="utf-8")

    missing_file = raw_dir / "old.md"

    settings = StubSettings()
    settings.raw_data_dir = str(raw_dir)
    settings.upload_dir = str(upload_dir)

    indexed_documents = [
        {
            "file_path": str(disk_file.resolve()),
            "filename": disk_file.name,
            "source_label": "raw",
            "category": "general",
            "file_type": "md",
            "chunk_count": 2,
            "updated_at": None,
        },
        {
            "file_path": str(missing_file.resolve()),
            "filename": missing_file.name,
            "source_label": "raw",
            "category": "general",
            "file_type": "md",
            "chunk_count": 1,
            "updated_at": None,
        },
    ]

    monkeypatch.setattr(documents_route, "get_settings", lambda: settings)
    monkeypatch.setattr(documents_route, "get_vector_store", lambda: StubVectorStore(indexed_documents))

    documents = documents_route._build_document_inventory()
    by_name = {item["filename"]: item for item in documents}

    assert by_name["notes.md"]["status"] == "indexed"
    assert by_name["old.md"]["status"] == "orphaned_index"


def test_sanitize_label_removes_path_separators() -> None:
    assert documents_route._sanitize_label("../prod/api", default="general") == "prod api"
