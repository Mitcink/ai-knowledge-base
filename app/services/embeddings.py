import httpx
from openai import OpenAI
from openai import NotFoundError

from app.config.settings import get_settings


class EmbeddingClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.embedding_model
        self._api_key = settings.embedding_api_key
        self._base_url = settings.embedding_base_url.rstrip("/")
        self._client = OpenAI(
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if "open.bigmodel.cn" in self._base_url:
            return self._embed_texts_with_httpx(texts)
        try:
            response = self._client.embeddings.create(model=self._model, input=texts)
        except NotFoundError as exc:
            settings = get_settings()
            raise RuntimeError(
                "Embedding request returned 404. Check EMBEDDING_BASE_URL and EMBEDDING_MODEL. "
                f"Current values: EMBEDDING_BASE_URL={settings.embedding_base_url}, "
                f"EMBEDDING_MODEL={settings.embedding_model}"
            ) from exc
        return [item.embedding for item in response.data]

    def _embed_texts_with_httpx(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            f"{self._base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "input": texts,
            },
            timeout=60.0,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                "Embedding request failed. "
                f"status={response.status_code}, body={response.text}"
            )

        payload = response.json()
        data = payload.get("data")
        if not isinstance(data, list) or not data:
            raise RuntimeError(f"Unexpected embedding response: {payload}")

        embeddings = []
        for item in data:
            embedding = item.get("embedding") if isinstance(item, dict) else None
            if not isinstance(embedding, list):
                raise RuntimeError(f"Unexpected embedding item: {item}")
            embeddings.append(embedding)
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


_embedding_client: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client

