from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path
from urllib.parse import urlparse

from config.settings import get_settings


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, data: bytes, category: str, extension: str = ".jpg") -> str:
        safe_extension = extension if extension.startswith(".") else f".{extension}"
        folder = self.settings.storage_dir / category
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}{safe_extension}"
        path = folder / filename
        path.write_bytes(data)

        supabase_url = self._try_upload_to_supabase(path, category, filename)
        if supabase_url:
            return supabase_url

        return f"{self.settings.api_base_url.rstrip('/')}/storage/{category}/{filename}"

    def local_path_from_url(self, url: str) -> Path | None:
        parsed = urlparse(url)
        if parsed.path.startswith("/storage/"):
            relative = parsed.path.removeprefix("/storage/")
            return self.settings.storage_dir / relative
        if url.startswith("file://"):
            return Path(parsed.path)
        return None

    def get_bytes_if_local(self, url: str) -> bytes | None:
        path = self.local_path_from_url(url)
        if path and path.exists():
            return path.read_bytes()
        return None

    def _try_upload_to_supabase(self, path: Path, category: str, filename: str) -> str | None:
        if not (self.settings.supabase_url and self.settings.supabase_key and self.settings.storage_bucket):
            return None

        try:
            from supabase import create_client
        except ImportError:
            return None

        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        object_name = f"{category}/{filename}"
        client = create_client(self.settings.supabase_url, self.settings.supabase_key)
        client.storage.from_(self.settings.storage_bucket).upload(
            object_name,
            path.read_bytes(),
            file_options={"content-type": content_type, "upsert": "true"},
        )
        return client.storage.from_(self.settings.storage_bucket).get_public_url(object_name)


storage_service = StorageService()
