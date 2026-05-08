from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from backend.app.core.security import AuthenticatedUser, require_owner
from backend.app.schemas.common_schema import success_response
from backend.app.services.image_storage_service import ImageStorageService


router = APIRouter()


@router.post("/images/upload")
def upload_image(
    file: UploadFile = File(..., description="Image file"),
    product_seq: int | None = Form(default=None),
    subfolder: str | None = Form(default=None),
    _: AuthenticatedUser = Depends(require_owner),
) -> dict:
    data = ImageStorageService().upload_image(file, product_seq=product_seq, subfolder=subfolder)
    return success_response(data)


@router.get("/images")
def list_images(
    subfolder: str | None = Query(default=None),
    _: AuthenticatedUser = Depends(require_owner),
) -> dict:
    data = ImageStorageService().list_images(subfolder=subfolder)
    return success_response(data)


@router.get("/images/{file_name}")
def get_image(
    file_name: str,
    subfolder: str | None = Query(default=None),
    _: AuthenticatedUser = Depends(require_owner),
) -> dict:
    data = ImageStorageService().get_image(file_name, subfolder=subfolder)
    return success_response(data)


@router.put("/images/{file_name}")
def update_image(
    file_name: str,
    file: UploadFile = File(..., description="Replacement image file"),
    subfolder: str | None = Form(default=None),
    _: AuthenticatedUser = Depends(require_owner),
) -> dict:
    data = ImageStorageService().update_image(file_name, file, subfolder=subfolder)
    return success_response(data)


@router.delete("/images/{file_name}")
def delete_image(
    file_name: str,
    subfolder: str | None = Query(default=None),
    _: AuthenticatedUser = Depends(require_owner),
) -> dict:
    data = ImageStorageService().delete_image(file_name, subfolder=subfolder)
    return success_response(data)
