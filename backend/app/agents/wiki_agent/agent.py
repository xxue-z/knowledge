import logging
from uuid import UUID

from app.mcps import AgentCapability, MCPRequest, MCPResponse, get_registry
from app.services.wiki_service import WikiService
from app.models.schemas import UserContext, WikiPageCreate, WikiPageUpdate
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class WikiAgent:
    """Wiki Agent - Wiki 文档管理服务"""
    
    CAPABILITY = AgentCapability(
        agent_id="wiki_agent",
        name="Wiki Agent",
        description="Wiki 文档管理服务，支持文档搜索、创建、更新、删除",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "get_page", "create_page", "update_page", "delete_page", "list_pages", "get_versions"]
                },
                "query": {"type": "string"},
                "page_id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "slug": {"type": "string"},
                "parent_id": {"type": "string"},
                "sensitivity": {"type": "string", "enum": ["public", "internal", "confidential", "secret"]},
                "dept_id": {"type": "string"},
                "page": {"type": "integer"},
                "page_size": {"type": "integer"}
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "slug": {"type": "string"},
                "parent_id": {"type": "string"},
                "sensitivity": {"type": "string"},
                "dept_id": {"type": "string"},
                "created_by": {"type": "string"},
                "updated_by": {"type": "string"},
                "created_at": {"type": "string"},
                "updated_at": {"type": "string"},
                "items": {"type": "array"},
                "total": {"type": "integer"}
            }
        },
        supported_intents=["PURE_KB", "HYBRID"],
        version="1.0",
        priority=100
    )
    
    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user
        self.wiki_service = WikiService(db, user)
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """处理 MCP 请求"""
        action = request.params.get("action")
        
        try:
            if action == "search":
                query = request.params.get("query", "")
                page = request.params.get("page", 1)
                page_size = request.params.get("page_size", 20)
                
                pages = await self.wiki_service.search(query, page, page_size)
                results = [{
                    "id": str(page.id),
                    "title": page.title,
                    "content": page.content[:200] + "..." if len(page.content) > 200 else page.content,
                    "slug": page.slug,
                    "sensitivity": page.sensitivity,
                    "created_at": str(page.created_at)
                } for page in pages]
                
                return MCPResponse(
                    success=True,
                    data={"items": results, "total": len(results)},
                    sources=[{"type": "wiki", "action": "search", "query": query}],
                    confidence=0.8
                )
            
            elif action == "get_page":
                page_id = request.params.get("page_id")
                page = await self.wiki_service.get_page(UUID(page_id))
                
                if page:
                    return MCPResponse(
                        success=True,
                        data={
                            "id": str(page.id),
                            "title": page.title,
                            "content": page.content,
                            "slug": page.slug,
                            "parent_id": str(page.parent_id) if page.parent_id else None,
                            "sensitivity": page.sensitivity,
                            "dept_id": page.dept_id,
                            "created_by": page.created_by,
                            "updated_by": page.updated_by,
                            "created_at": str(page.created_at),
                            "updated_at": str(page.updated_at)
                        },
                        sources=[{"type": "wiki", "page_id": page_id}],
                        confidence=1.0
                    )
                return MCPResponse(
                    success=False,
                    error=f"页面 {page_id} 不存在",
                    confidence=0.0
                )
            
            elif action == "create_page":
                data = WikiPageCreate(
                    title=request.params.get("title"),
                    content=request.params.get("content"),
                    slug=request.params.get("slug"),
                    parent_id=UUID(request.params.get("parent_id")) if request.params.get("parent_id") else None,
                    sensitivity=request.params.get("sensitivity", "public"),
                    dept_id=request.params.get("dept_id")
                )
                
                page = await self.wiki_service.create_page(data)
                return MCPResponse(
                    success=True,
                    data={
                        "id": str(page.id),
                        "title": page.title,
                        "slug": page.slug
                    },
                    sources=[{"type": "wiki", "action": "create", "page_id": str(page.id)}],
                    confidence=1.0
                )
            
            elif action == "update_page":
                page_id = request.params.get("page_id")
                data = WikiPageUpdate(
                    title=request.params.get("title"),
                    content=request.params.get("content"),
                    parent_id=UUID(request.params.get("parent_id")) if request.params.get("parent_id") else None,
                    sensitivity=request.params.get("sensitivity"),
                    edit_summary=request.params.get("edit_summary")
                )
                
                page = await self.wiki_service.update_page(UUID(page_id), data)
                if page:
                    return MCPResponse(
                        success=True,
                        data={
                            "id": str(page.id),
                            "title": page.title,
                            "updated_at": str(page.updated_at)
                        },
                        sources=[{"type": "wiki", "action": "update", "page_id": page_id}],
                        confidence=1.0
                    )
                return MCPResponse(
                    success=False,
                    error="更新失败，页面不存在或权限不足",
                    confidence=0.0
                )
            
            elif action == "delete_page":
                page_id = request.params.get("page_id")
                success = await self.wiki_service.delete_page(UUID(page_id))
                
                return MCPResponse(
                    success=success,
                    data={"page_id": page_id},
                    sources=[{"type": "wiki", "action": "delete", "page_id": page_id}],
                    confidence=1.0 if success else 0.0
                )
            
            elif action == "list_pages":
                page = request.params.get("page", 1)
                page_size = request.params.get("page_size", 20)
                parent_id = request.params.get("parent_id")
                
                pages = await self.wiki_service.list_pages(
                    parent_id=UUID(parent_id) if parent_id else None,
                    page=page,
                    page_size=page_size
                )
                
                results = [{
                    "id": str(page.id),
                    "title": page.title,
                    "slug": page.slug,
                    "sensitivity": page.sensitivity,
                    "created_by": page.created_by,
                    "created_at": str(page.created_at)
                } for page in pages]
                
                return MCPResponse(
                    success=True,
                    data={"items": results, "total": len(results)},
                    sources=[{"type": "wiki", "action": "list"}],
                    confidence=1.0
                )
            
            elif action == "get_versions":
                page_id = request.params.get("page_id")
                versions = await self.wiki_service.get_versions(UUID(page_id))
                
                results = [{
                    "version": v.version,
                    "title": v.title,
                    "edited_by": v.edited_by,
                    "edit_summary": v.edit_summary,
                    "created_at": str(v.created_at)
                } for v in versions]
                
                return MCPResponse(
                    success=True,
                    data={"items": results, "total": len(results)},
                    sources=[{"type": "wiki", "action": "versions", "page_id": page_id}],
                    confidence=1.0
                )
            
            else:
                return MCPResponse(
                    success=False,
                    error=f"不支持的操作: {action}",
                    confidence=0.0
                )
        
        except Exception as e:
            logger.error(f"WikiAgent error: {str(e)}")
            return MCPResponse(
                success=False,
                error=str(e),
                confidence=0.0
            )


def register_agent() -> None:
    """注册 Wiki Agent - 注册类而不是实例"""
    registry = get_registry()
    registry.register(WikiAgent.CAPABILITY, WikiAgent)
