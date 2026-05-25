from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from app.services.tags_service import TagsService
from app.dal import WikiTagRepository, WikiPageRepository
from app.dal import get_adapter
from app.core.security import get_current_active_user
from app.models.schemas import UserContext

router = APIRouter()


async def get_tags_service() -> TagsService:
    adapter = get_adapter()
    return TagsService(WikiTagRepository(adapter), WikiPageRepository(adapter))


@router.get("/")
async def list_tags(service: TagsService = Depends(get_tags_service)):
    return await service.list_tags()


@router.get("/tree")
async def get_tag_tree(service: TagsService = Depends(get_tags_service)):
    return await service.get_tag_tree()


@router.post("/")
async def create_tag(
    name: str,
    color: str = "#3B82F6",
    description: str = None,
    parent_id: UUID = None,
    current_user: UserContext = Depends(get_current_active_user),
    service: TagsService = Depends(get_tags_service),
):
    try:
        tag = await service.create_tag(name, color, description, parent_id, current_user.username)
        return {"id": str(tag.id), "name": tag.name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{tag_id}")
async def update_tag(
    tag_id: UUID,
    name: str,
    color: str,
    description: str = None,
    parent_id: UUID = None,
    service: TagsService = Depends(get_tags_service),
):
    tag = await service.update_tag(tag_id, name, color, description, parent_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"id": str(tag.id)}


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: UUID,
    service: TagsService = Depends(get_tags_service),
):
    if not await service.delete_tag(tag_id):
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"success": True}


@router.post("/pages/{page_id}/tags/{tag_id}")
async def add_tag_to_page(
    page_id: UUID,
    tag_id: UUID,
    service: TagsService = Depends(get_tags_service),
):
    success = await service.add_tag_to_page(page_id, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Page or tag not found")
    return {"success": True}


@router.delete("/pages/{page_id}/tags/{tag_id}")
async def remove_tag_from_page(
    page_id: UUID,
    tag_id: UUID,
    service: TagsService = Depends(get_tags_service),
):
    success = await service.remove_tag_from_page(page_id, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Page or tag not found")
    return {"success": True}
