from __future__ import annotations

from io import BytesIO
from pathlib import PurePosixPath
import re

import httpx
from fastapi import HTTPException, UploadFile

from backend.app.core.config import settings


SUBFOLDER_PATTERN = re.compile(r"^[A-Za-z0-9_/-]+$")
SAFE_FILE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


class ImageStorageService:
    def validate_image_extension(self, file_name: str) -> str:
        extension = PurePosixPath(file_name).suffix.lower().lstrip(".")
        if extension not in settings.allowed_image_extensions:
            raise HTTPException(status_code=400, detail="unsupported image extension")
        return extension

    def validate_subfolder(self, subfolder: str | None) -> str | None:
        if not subfolder:
            return None
        value = subfolder.strip()
        if not value or value.startswith(("/", "\\")) or ".." in value or "\\" in value:
            raise HTTPException(status_code=400, detail="invalid subfolder")
        if not SUBFOLDER_PATTERN.fullmatch(value):
            raise HTTPException(status_code=400, detail="invalid subfolder")
        return value

    def validate_file_name(self, file_name: str) -> str:
        value = (file_name or "").strip()
        if (
            not value
            or value.startswith(("/", "\\"))
            or ".." in value
            or "/" in value
            or "\\" in value
        ):
            raise HTTPException(status_code=400, detail="invalid file name")
        if SAFE_FILE_NAME_PATTERN.search(value):
            raise HTTPException(status_code=400, detail="invalid file name")
        self.validate_image_extension(value)
        return value

    def sanitize_file_name(self, file_name: str) -> str:
        raw_name = (file_name or "").strip()
        if not raw_name or "/" in raw_name or "\\" in raw_name or ".." in raw_name:
            raise HTTPException(status_code=400, detail="invalid file name")

        path = PurePosixPath(raw_name)
        stem = SAFE_FILE_NAME_PATTERN.sub("_", path.stem).strip("._-")
        if not stem:
            raise HTTPException(status_code=400, detail="invalid file name")

        extension = self.validate_image_extension(raw_name)
        sanitized_name = f"{stem}.{extension}"
        self.validate_file_name(sanitized_name)
        return sanitized_name

    def validate_image_size(self, upload: UploadFile) -> int:
        upload.file.seek(0, 2)
        size = upload.file.tell()
        upload.file.seek(0)
        max_size_bytes = settings.image_max_size_mb * 1024 * 1024
        if size > max_size_bytes:
            raise HTTPException(status_code=400, detail="image file too large")
        return size

    def validate_content_type(self, upload: UploadFile) -> None:
        content_type = (upload.content_type or "").strip().lower()
        if content_type and not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="invalid image content type")

    def _prepare_upload_file(self, upload: UploadFile) -> tuple[str, bytes]:
        sanitized_name = self.sanitize_file_name(upload.filename or "")
        self.validate_content_type(upload)
        self.validate_image_size(upload)
        upload.file.seek(0)
        file_bytes = upload.file.read()
        upload.file.seek(0)
        if not file_bytes:
            raise HTTPException(status_code=400, detail="invalid image file")
        return sanitized_name, file_bytes

    def _handle_storage_response(
        self,
        response: httpx.Response,
        *,
        action: str,
        require_file_url: bool = False,
    ) -> dict:
        try:
            payload = response.json()
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="invalid image storage response") from exc

        if response.status_code >= 400 or payload.get("result") == "Error":
            if action in {"get", "update", "delete"}:
                raise HTTPException(status_code=404, detail="image not found")
            raise HTTPException(status_code=502, detail="image storage error")

        if payload.get("result") != "OK":
            raise HTTPException(status_code=502, detail="image storage error")

        if require_file_url and not payload.get("file_url"):
            raise HTTPException(status_code=502, detail="image storage response missing file_url")

        return payload

    def _request_storage(
        self,
        method: str,
        *,
        action: str,
        params: dict | None = None,
        data: dict | None = None,
        files: dict | None = None,
        require_file_url: bool = False,
    ) -> dict:
        request_params = {"action": action, **(params or {})}
        request_data = {"action": action, **(data or {})}

        try:
            with httpx.Client(timeout=settings.image_upload_timeout_seconds) as client:
                if method.upper() == "GET":
                    response = client.get(settings.image_upload_url, params=request_params)
                elif method.upper() == "DELETE":
                    response = client.delete(settings.image_upload_url, params=request_params)
                else:
                    response = client.post(
                        settings.image_upload_url,
                        data=request_data,
                        files=files,
                    )
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail="image storage timeout") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="image storage error") from exc

        return self._handle_storage_response(
            response,
            action=action,
            require_file_url=require_file_url,
        )

    def upload_image(
        self,
        upload: UploadFile,
        *,
        product_seq: int | None = None,
        subfolder: str | None = None,
    ) -> dict:
        sanitized_name, file_bytes = self._prepare_upload_file(upload)
        normalized_subfolder = self.validate_subfolder(subfolder)
        payload = self._request_storage(
            "POST",
            action="upload",
            data={
                **({"product_seq": str(product_seq)} if product_seq is not None else {}),
                **({"subfolder": normalized_subfolder} if normalized_subfolder else {}),
            },
            files={
                "file": (
                    sanitized_name,
                    BytesIO(file_bytes),
                    upload.content_type or "application/octet-stream",
                )
            },
            require_file_url=True,
        )
        return {
            "file_url": payload["file_url"],
            "file_name": payload.get("file_name", sanitized_name),
            "file_type": payload.get("file_type", "image"),
            "subfolder": payload.get("subfolder", normalized_subfolder),
        }

    def list_images(self, *, subfolder: str | None = None) -> dict:
        normalized_subfolder = self.validate_subfolder(subfolder)
        payload = self._request_storage(
            "GET",
            action="list",
            params={**({"subfolder": normalized_subfolder} if normalized_subfolder else {})},
        )
        files = []
        for row in payload.get("files", []):
            files.append(
                {
                    "file_name": row.get("file_name"),
                    "file_type": row.get("file_type"),
                    "subfolder": row.get("subfolder"),
                    "file_url": row.get("file_url"),
                    "file_size": row.get("file_size"),
                    "modified_at": row.get("modified_at"),
                }
            )
        return {
            "subfolder": payload.get("subfolder", normalized_subfolder),
            "count": payload.get("count", len(files)),
            "files": files,
        }

    def get_image(self, file_name: str, *, subfolder: str | None = None) -> dict:
        normalized_file_name = self.validate_file_name(file_name)
        normalized_subfolder = self.validate_subfolder(subfolder)
        payload = self._request_storage(
            "GET",
            action="get",
            params={
                "file_name": normalized_file_name,
                **({"subfolder": normalized_subfolder} if normalized_subfolder else {}),
            },
            require_file_url=True,
        )
        return {
            "file_name": payload.get("file_name", normalized_file_name),
            "file_type": payload.get("file_type"),
            "subfolder": payload.get("subfolder", normalized_subfolder),
            "file_url": payload["file_url"],
            "file_size": payload.get("file_size"),
            "modified_at": payload.get("modified_at"),
        }

    def update_image(self, file_name: str, upload: UploadFile, *, subfolder: str | None = None) -> dict:
        normalized_file_name = self.validate_file_name(file_name)
        sanitized_name, file_bytes = self._prepare_upload_file(upload)
        normalized_subfolder = self.validate_subfolder(subfolder)

        current_extension = self.validate_image_extension(normalized_file_name)
        new_extension = self.validate_image_extension(sanitized_name)
        if current_extension != new_extension:
            raise HTTPException(status_code=400, detail="image extension mismatch")

        payload = self._request_storage(
            "POST",
            action="update",
            data={
                "file_name": normalized_file_name,
                **({"subfolder": normalized_subfolder} if normalized_subfolder else {}),
            },
            files={
                "file": (
                    sanitized_name,
                    BytesIO(file_bytes),
                    upload.content_type or "application/octet-stream",
                )
            },
            require_file_url=True,
        )
        return {
            "file_url": payload["file_url"],
            "file_name": payload.get("file_name", normalized_file_name),
            "file_type": payload.get("file_type", "image"),
            "subfolder": payload.get("subfolder", normalized_subfolder),
        }

    def delete_image(self, file_name: str, *, subfolder: str | None = None) -> dict:
        normalized_file_name = self.validate_file_name(file_name)
        normalized_subfolder = self.validate_subfolder(subfolder)
        payload = self._request_storage(
            "DELETE",
            action="delete",
            params={
                "file_name": normalized_file_name,
                **({"subfolder": normalized_subfolder} if normalized_subfolder else {}),
            },
        )
        return {
            "file_name": payload.get("file_name", normalized_file_name),
            "subfolder": payload.get("subfolder", normalized_subfolder),
        }


ImageUploadService = ImageStorageService
