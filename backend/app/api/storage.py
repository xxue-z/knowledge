from fastapi import APIRouter, Depends
from uuid import UUID
from app.services.storage_service import StorageService
from app.services import get_storage_service

router = APIRouter()


@router.post("/upload-url")
async def get_upload_url(
    file_path: str,
    expires_in: int = 900,
    service: StorageService = Depends(get_storage_service),
):
    url = await service.get_upload_url(file_path, expires_in)
    return {"url": url.url, "expires_in": url.expires_in}


@router.get("/download-url/{file_id}")
async def get_download_url(
    file_id: UUID,
    file_path: str,
    expires_in: int = 300,
    service: StorageService = Depends(get_storage_service),
):
    url = await service.get_download_url(file_path, expires_in)
    return {"url": url.url, "expires_in": url.expires_in}


@router.post("/test")
async def test_connection(
    service: StorageService = Depends(get_storage_service),
):
    success, message = await service.test_connection()
    return {"success": success, "message": message}


@router.get("/status")
async def get_storage_status(
    service: StorageService = Depends(get_storage_service),
):
    configured = await service.is_configured()
    return {"configured": configured}
