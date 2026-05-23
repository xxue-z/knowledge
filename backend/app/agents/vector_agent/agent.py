import logging

from app.mcps import AgentCapability, MCPRequest, MCPResponse, get_registry
from app.services.vector_service import VectorService
from app.models.schemas import UserContext

logger = logging.getLogger(__name__)


class VectorAgent:
    """向量 Agent - 语义检索服务"""
    
    CAPABILITY = AgentCapability(
        agent_id="vector_agent",
        name="向量 Agent",
        description="向量数据库语义检索服务，支持问答匹配、文档相似度搜索",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "insert", "delete", "update"]
                },
                "query": {"type": "string"},
                "text": {"type": "string"},
                "embedding_id": {"type": "string"},
                "document_id": {"type": "string"},
                "metadata": {"type": "object"},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 50},
                "threshold": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "document_id": {"type": "string"},
                            "content": {"type": "string"},
                            "score": {"type": "number"},
                            "metadata": {"type": "object"}
                        }
                    }
                },
                "inserted": {"type": "boolean"},
                "deleted": {"type": "boolean"},
                "updated": {"type": "boolean"}
            }
        },
        supported_intents=["PURE_KB", "HYBRID"],
        version="1.0",
        priority=100
    )
    
    def __init__(self, db_session, user: UserContext):
        self.user = user
        self.vector_service = VectorService(user)
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """处理 MCP 请求"""
        action = request.params.get("action")
        
        try:
            if action == "search":
                query = request.params.get("query", "")
                top_k = request.params.get("top_k", 5)
                threshold = request.params.get("threshold", 0.5)
                
                results = await self.vector_service.search(query, top_k, threshold)
                formatted_results = [{
                    "document_id": r.get("document_id"),
                    "content": r.get("content", "")[:300] + "..." if len(r.get("content", "")) > 300 else r.get("content", ""),
                    "score": r.get("score"),
                    "metadata": r.get("metadata", {})
                } for r in results]
                
                return MCPResponse(
                    success=True,
                    data={"results": formatted_results},
                    sources=[{"type": "vector", "action": "search", "query": query}],
                    confidence=min(0.5 + (len(results) * 0.1), 0.9)
                )
            
            elif action == "insert":
                text = request.params.get("text")
                document_id = request.params.get("document_id")
                metadata = request.params.get("metadata", {})
                
                success = await self.vector_service.insert(text, document_id, metadata)
                return MCPResponse(
                    success=success,
                    data={"inserted": success, "document_id": document_id},
                    sources=[{"type": "vector", "action": "insert", "document_id": document_id}],
                    confidence=1.0 if success else 0.0
                )
            
            elif action == "delete":
                document_id = request.params.get("document_id")
                
                success = await self.vector_service.delete(document_id)
                return MCPResponse(
                    success=success,
                    data={"deleted": success, "document_id": document_id},
                    sources=[{"type": "vector", "action": "delete", "document_id": document_id}],
                    confidence=1.0 if success else 0.0
                )
            
            elif action == "update":
                text = request.params.get("text")
                document_id = request.params.get("document_id")
                metadata = request.params.get("metadata", {})
                
                success = await self.vector_service.update(document_id, text, metadata)
                return MCPResponse(
                    success=success,
                    data={"updated": success, "document_id": document_id},
                    sources=[{"type": "vector", "action": "update", "document_id": document_id}],
                    confidence=1.0 if success else 0.0
                )
            
            else:
                return MCPResponse(
                    success=False,
                    error=f"不支持的操作: {action}",
                    confidence=0.0
                )
        
        except Exception as e:
            logger.error(f"VectorAgent error: {str(e)}")
            return MCPResponse(
                success=False,
                error=str(e),
                confidence=0.0
            )


def register_agent() -> None:
    """注册向量 Agent - 注册类而不是实例"""
    registry = get_registry()
    registry.register(VectorAgent.CAPABILITY, VectorAgent)
