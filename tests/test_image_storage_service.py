from io import BytesIO

import httpx
import pytest

from backend.app.core.config import settings
from backend.app.services.image_storage_service import ImageStorageService


class UploadStub:
    def __init__(self, filename: str, content: bytes, content_type: str | None = "image/jpeg"):
        self.filename = filename
        self.content_type = content_type
        self.file = BytesIO(content)


class DummyResponse:
    def __init__(self, payload: dict | None = None, *, status_code: int = 200, raises_json: bool = False):
        self._payload = payload or {}
        self.status_code = status_code
        self._raises_json = raises_json

    def json(self):
        if self._raises_json:
            raise ValueError("invalid json")
        return self._payload


class DummyClient:
    def __init__(self, *args, response: DummyResponse | None = None, error: Exception | None = None, **kwargs):
        self.response = response or DummyResponse()
        self.error = error
        self.calls: list[tuple[str, dict]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, params=None):
        self.calls.append(("GET", {"url": url, "params": params}))
        if self.error:
            raise self.error
        return self.response

    def post(self, url, data=None, files=None):
        self.calls.append(("POST", {"url": url, "data": data, "files": files}))
        if self.error:
            raise self.error
        return self.response

    def delete(self, url, params=None):
        self.calls.append(("DELETE", {"url": url, "params": params}))
        if self.error:
            raise self.error
        return self.response


def test_upload_image_success(monkeypatch):
    dummy_client = DummyClient(
        response=DummyResponse(
            {
                "result": "OK",
                "action": "upload",
                "file_url": "https://cdn.test/products/1/product_1_apple.jpg",
                "file_name": "product_1_apple.jpg",
                "file_type": "image",
                "subfolder": "products/1",
                "saved_path": "/share/Web/images/products/1/product_1_apple.jpg",
                "file_path": "/share/Web/images/products/1/product_1_apple.jpg",
            }
        )
    )
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: dummy_client)

    service = ImageStorageService()
    result = service.upload_image(UploadStub("apple.jpg", b"image-bytes"), product_seq=1, subfolder="products/1")
    assert result == {
        "file_url": "https://cdn.test/products/1/product_1_apple.jpg",
        "file_name": "product_1_apple.jpg",
        "file_type": "image",
        "subfolder": "products/1",
    }


def test_list_images_success(monkeypatch):
    dummy_client = DummyClient(
        response=DummyResponse(
            {
                "result": "OK",
                "action": "list",
                "subfolder": "products/1",
                "count": 1,
                "files": [
                    {
                        "file_name": "product_1_apple.jpg",
                        "file_type": "image",
                        "subfolder": "products/1",
                        "file_url": "https://cdn.test/products/1/product_1_apple.jpg",
                        "file_size": 1234,
                        "modified_at": "2026-05-08T10:30:00+09:00",
                        "saved_path": "/share/Web/images/products/1/product_1_apple.jpg",
                    }
                ],
            }
        )
    )
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: dummy_client)

    result = ImageStorageService().list_images(subfolder="products/1")
    assert result["count"] == 1
    assert result["files"][0]["file_url"] == "https://cdn.test/products/1/product_1_apple.jpg"
    assert "saved_path" not in result["files"][0]


def test_get_image_success(monkeypatch):
    dummy_client = DummyClient(
        response=DummyResponse(
            {
                "result": "OK",
                "action": "get",
                "file_name": "product_1_apple.jpg",
                "file_type": "image",
                "subfolder": "products/1",
                "file_url": "https://cdn.test/products/1/product_1_apple.jpg",
                "file_size": 1234,
                "modified_at": "2026-05-08T10:30:00+09:00",
            }
        )
    )
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: dummy_client)

    result = ImageStorageService().get_image("product_1_apple.jpg", subfolder="products/1")
    assert result["file_name"] == "product_1_apple.jpg"
    assert result["file_size"] == 1234


def test_update_image_success(monkeypatch):
    dummy_client = DummyClient(
        response=DummyResponse(
            {
                "result": "OK",
                "action": "update",
                "file_url": "https://cdn.test/products/1/product_1_apple.jpg",
                "file_name": "product_1_apple.jpg",
                "file_type": "image",
                "subfolder": "products/1",
            }
        )
    )
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: dummy_client)

    result = ImageStorageService().update_image(
        "product_1_apple.jpg",
        UploadStub("replacement.jpg", b"new-image"),
        subfolder="products/1",
    )
    assert result["file_url"] == "https://cdn.test/products/1/product_1_apple.jpg"


def test_delete_image_success(monkeypatch):
    dummy_client = DummyClient(
        response=DummyResponse(
            {
                "result": "OK",
                "action": "delete",
                "file_name": "product_1_apple.jpg",
                "subfolder": "products/1",
            }
        )
    )
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: dummy_client)

    result = ImageStorageService().delete_image("product_1_apple.jpg", subfolder="products/1")
    assert result == {"file_name": "product_1_apple.jpg", "subfolder": "products/1"}


def test_unsupported_extension_returns_400():
    with pytest.raises(Exception) as exc_info:
        ImageStorageService().upload_image(UploadStub("notes.txt", b"bad-file", "text/plain"))
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "unsupported image extension"


def test_invalid_subfolder_returns_400():
    with pytest.raises(Exception) as exc_info:
        ImageStorageService().list_images(subfolder="../secrets")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "invalid subfolder"


def test_absolute_subfolder_returns_400():
    with pytest.raises(Exception) as exc_info:
        ImageStorageService().list_images(subfolder="/etc/images")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "invalid subfolder"


def test_invalid_file_name_returns_400():
    with pytest.raises(Exception) as exc_info:
        ImageStorageService().get_image("../product.jpg", subfolder="products/1")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "invalid file name"


def test_file_too_large_returns_400(monkeypatch):
    monkeypatch.setattr(settings, "image_max_size_mb", 1)
    oversized = UploadStub("apple.jpg", b"a" * (2 * 1024 * 1024))

    with pytest.raises(Exception) as exc_info:
        ImageStorageService().upload_image(oversized)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "image file too large"


def test_invalid_content_type_returns_400():
    with pytest.raises(Exception) as exc_info:
        ImageStorageService().upload_image(UploadStub("apple.jpg", b"image", "application/pdf"))
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "invalid image content type"


def test_nas_result_error_returns_502(monkeypatch):
    dummy_client = DummyClient(response=DummyResponse({"result": "Error", "errorMsg": "upload failed"}))
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: dummy_client)

    with pytest.raises(Exception) as exc_info:
        ImageStorageService().upload_image(UploadStub("apple.jpg", b"image"))
    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "image storage error"


def test_nas_timeout_returns_504(monkeypatch):
    dummy_client = DummyClient(error=httpx.TimeoutException("timeout"))
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: dummy_client)

    with pytest.raises(Exception) as exc_info:
        ImageStorageService().upload_image(UploadStub("apple.jpg", b"image"))
    assert exc_info.value.status_code == 504
    assert exc_info.value.detail == "image storage timeout"


def test_nas_json_parse_failure_returns_502(monkeypatch):
    dummy_client = DummyClient(response=DummyResponse(raises_json=True))
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: dummy_client)

    with pytest.raises(Exception) as exc_info:
        ImageStorageService().upload_image(UploadStub("apple.jpg", b"image"))
    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "invalid image storage response"


def test_nas_missing_file_url_returns_502(monkeypatch):
    dummy_client = DummyClient(response=DummyResponse({"result": "OK", "action": "upload"}))
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: dummy_client)

    with pytest.raises(Exception) as exc_info:
        ImageStorageService().upload_image(UploadStub("apple.jpg", b"image"))
    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "image storage response missing file_url"
