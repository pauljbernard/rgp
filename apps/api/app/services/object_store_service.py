from pathlib import Path

from app.core.config import settings


class ObjectStoreService:
    def put_text(self, object_key: str, content: str) -> str:
        path = self._resolve_path(object_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return object_key

    def get_text(self, object_key: str) -> str:
        return self._resolve_path(object_key).read_text(encoding="utf-8")

    def exists(self, object_key: str) -> bool:
        return self._resolve_path(object_key).exists()

    def _resolve_path(self, object_key: str) -> Path:
        return Path(settings.object_store_root) / object_key


object_store_service = ObjectStoreService()
