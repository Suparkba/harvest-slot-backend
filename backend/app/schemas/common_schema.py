from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    data: T
    message: str = "success"
    error: Any = None

    model_config = ConfigDict(from_attributes=True)


def success_response(data: Any, message: str = "success") -> dict[str, Any]:
    return {"data": data, "message": message, "error": None}


def error_response(message: str, error: Any, data: Any | None = None) -> dict[str, Any]:
    return {"data": data if data is not None else {}, "message": message, "error": error}
