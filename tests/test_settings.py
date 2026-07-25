import os

from app.config.settings import Settings


def test_settings_validate_chunk_overlap() -> None:
    old_chunk_size = os.environ.get("MAX_CHUNK_SIZE")
    old_overlap = os.environ.get("CHUNK_OVERLAP")
    try:
        os.environ["MAX_CHUNK_SIZE"] = "100"
        os.environ["CHUNK_OVERLAP"] = "100"
        try:
            Settings()
        except ValueError as exc:
            assert "CHUNK_OVERLAP must be smaller than MAX_CHUNK_SIZE" in str(exc)
        else:
            raise AssertionError("Expected ValueError for invalid settings")
    finally:
        if old_chunk_size is None:
            os.environ.pop("MAX_CHUNK_SIZE", None)
        else:
            os.environ["MAX_CHUNK_SIZE"] = old_chunk_size
        if old_overlap is None:
            os.environ.pop("CHUNK_OVERLAP", None)
        else:
            os.environ["CHUNK_OVERLAP"] = old_overlap
