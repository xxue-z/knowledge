from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from pydantic import BaseModel
from app.services.chunking_service import ChunkingService
from app.dal import ChunkingRuleRepository
from app.dal import get_adapter
from app.core.security import get_current_active_user
from app.models.schemas import UserContext

router = APIRouter()


class ChunkingRuleCreate(BaseModel):
    name: str
    description: str = None
    rule_type: str
    rule_config: dict
    sort_order: int = 0


class ChunkingRuleUpdate(BaseModel):
    name: str
    description: str = None
    rule_type: str
    rule_config: dict
    is_active: bool = True


class ChunkingRuleReorder(BaseModel):
    orders: list[dict]


async def get_chunking_service(
    rule_repo: ChunkingRuleRepository = None,
) -> ChunkingService:
    adapter = get_adapter()
    return ChunkingService(ChunkingRuleRepository(adapter))


@router.get("/")
async def list_rules(service: ChunkingService = Depends(get_chunking_service)):
    return await service.list_rules()


@router.get("/active")
async def get_active_rules(service: ChunkingService = Depends(get_chunking_service)):
    return await service.get_active_rules()


@router.post("/")
async def create_rule(
    rule: ChunkingRuleCreate,
    current_user: UserContext = Depends(get_current_active_user),
    service: ChunkingService = Depends(get_chunking_service),
):
    new_rule = await service.create_rule(
        rule.name,
        rule.description,
        rule.rule_type,
        rule.rule_config,
        rule.sort_order,
        current_user.username,
    )
    return {"id": str(new_rule.id)}


@router.put("/{rule_id}")
async def update_rule(
    rule_id: UUID,
    rule: ChunkingRuleUpdate,
    service: ChunkingService = Depends(get_chunking_service),
):
    updated = await service.update_rule(
        rule_id,
        rule.name,
        rule.description,
        rule.rule_type,
        rule.rule_config,
        rule.is_active,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"id": str(updated.id)}


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: UUID,
    service: ChunkingService = Depends(get_chunking_service),
):
    if not await service.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"success": True}


@router.post("/reorder")
async def reorder_rules(
    data: ChunkingRuleReorder,
    service: ChunkingService = Depends(get_chunking_service),
):
    await service.reorder_rules(data.orders)
    return {"success": True}
