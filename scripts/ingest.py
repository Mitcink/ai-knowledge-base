from pathlib import Path

from app.config.settings import get_settings
from app.services.rag_service import get_rag_service


def main() -> None:
    settings = get_settings()
    data_dir = Path(settings.raw_data_dir)
    service = get_rag_service()
    summaries = service.ingest_directory(data_dir, source_label="raw")
    print(f"Ingested {len(summaries)} files from {data_dir}")
    for summary in summaries:
        print(summary)


if __name__ == "__main__":
    main()

