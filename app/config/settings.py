from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "knowledge_base"
    raw_data_dir: str = "./data/raw"
    processed_data_dir: str = "./data/processed"
    upload_dir: str = "./data/uploads"
    max_chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 6
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_server_port: int = 8501
    auto_ingest_on_startup: bool = True
    auto_ingest_source_label: str = "raw"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
