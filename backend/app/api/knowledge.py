from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID

from app.core.security import get_current_active_user
from app.models.schemas import (
    UserContext, NavNodeCreate, NavNodeUpdate, NavNodeResponse,
)
from app.server import get_knowledge_server, KnowledgeServer

router = APIRouter()


@router.get("/nav", response_model=list[NavNodeResponse])
async def get_navigation_tree(
    server: KnowledgeServer = Depends(get_knowledge_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    """获取知识导航树"""
    return await server.get_tree(current_user)


@router.post("/nav", response_model=NavNodeResponse, status_code=201)
async def create_nav_node(
    data: NavNodeCreate,
    server: KnowledgeServer = Depends(get_knowledge_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    """创建导航节点"""
    return await server.create_node(current_user, data)


@router.put("/nav/{node_id}", response_model=NavNodeResponse)
async def update_nav_node(
    node_id: UUID,
    data: NavNodeUpdate,
    server: KnowledgeServer = Depends(get_knowledge_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    """更新导航节点"""
    node = await server.update_node(current_user, node_id, data)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.delete("/nav/{node_id}", status_code=204)
async def delete_nav_node(
    node_id: UUID,
    server: KnowledgeServer = Depends(get_knowledge_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    """删除导航节点"""
    if not await server.delete_node(current_user, node_id):
        raise HTTPException(status_code=404, detail="Node not found")


@router.post("/nav/{node_id}/link")
async def link_content_to_nav(
    node_id: UUID,
    content_type: str = Query(..., pattern="^(wiki|conversation|external)$"),
    content_id: str = ...,
    server: KnowledgeServer = Depends(get_knowledge_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    """关联内容到导航节点"""
    return await server.link_content(current_user, node_id, content_type, content_id)
