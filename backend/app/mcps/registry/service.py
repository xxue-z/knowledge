import logging
from typing import Dict, List, Callable, Optional, Any, Type

from app.mcps.mcp_protocol import AgentCapability, MCPRequest, MCPResponse, MCPClient

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Agent 注册表"""
    
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
    
    def register(self, capability: AgentCapability, agent_class: Type) -> None:
        """注册 Agent - 注册 Agent 类，而不是实例"""
        self.agents[capability.agent_id] = {
            "capability": capability,
            "agent_class": agent_class
        }
        logger.info(f"Agent registered: {capability.agent_id}")
    
    def unregister(self, agent_id: str) -> bool:
        """注销 Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent unregistered: {agent_id}")
            return True
        return False
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取 Agent 信息"""
        return self.agents.get(agent_id)
    
    def find_by_intent(self, intent: str) -> List[Dict[str, Any]]:
        """根据意图查找支持的 Agent，按优先级排序"""
        candidates = []
        for agent_id, info in self.agents.items():
            if intent in info["capability"].supported_intents:
                candidates.append(info)
        
        candidates.sort(key=lambda x: x["capability"].priority)
        return candidates
    
    def get_all_capabilities(self) -> List[AgentCapability]:
        """获取所有 Agent 能力描述"""
        return [info["capability"] for info in self.agents.values()]
    
    def is_registered(self, agent_id: str) -> bool:
        """检查 Agent 是否已注册"""
        return agent_id in self.agents


class LocalMCPClient(MCPClient):
    """本地 MCP 客户端实现"""
    
    def __init__(self, registry: AgentRegistry, db_session=None, user_context=None):
        self.registry = registry
        self.db_session = db_session
        self.user_context = user_context
    
    def with_context(self, db_session, user_context):
        """创建带上下文的 MCP 客户端"""
        return LocalMCPClient(self.registry, db_session, user_context)
    
    async def call(self, agent_id: str, request: MCPRequest) -> MCPResponse:
        """调用指定 Agent - 动态实例化"""
        from app.core.trace import TraceManager
        
        agent_info = self.registry.get_agent(agent_id)
        if not agent_info:
            return MCPResponse(
                success=False,
                error=f"Agent not found: {agent_id}",
                trace_id=request.trace_id
            )
        
        span_id = TraceManager.create_span(f"agent:{agent_id}")
        
        if not request.trace_id:
            request.trace_id = TraceManager.get_trace_id()
        request.span_id = span_id
        
        # 使用请求中的上下文或客户端的上下文
        db_session = request.db_session or self.db_session
        user_context = request.user_context or self.user_context
        
        logger.info(
            f"MCP call: agent={agent_id}, action={request.action}, user={user_context.user_id if user_context else 'unknown'}, trace_id={request.trace_id}",
            extra={"trace_id": request.trace_id, "span_id": span_id}
        )
        
        try:
            agent_class = agent_info["agent_class"]
            # 动态实例化 Agent，传入当前用户和数据库会话
            agent = agent_class(db_session, user_context)
            result = await agent.handle_request(request)
            
            if isinstance(result, MCPResponse):
                result.trace_id = request.trace_id
                result.span_id = span_id
                return result
            elif isinstance(result, dict):
                return MCPResponse(
                    success=result.get("success", True),
                    data=result.get("data"),
                    error=result.get("error"),
                    sources=result.get("sources", []),
                    confidence=result.get("confidence", 0.0),
                    trace_id=request.trace_id,
                    span_id=span_id
                )
            else:
                return MCPResponse(
                    success=True,
                    data=result,
                    confidence=1.0,
                    trace_id=request.trace_id,
                    span_id=span_id
                )
        
        except Exception as e:
            logger.error(
                f"Agent call failed: agent={agent_id}, error={str(e)}",
                extra={"trace_id": request.trace_id, "span_id": span_id},
                exc_info=True
            )
            return MCPResponse(
                success=False,
                error=str(e),
                trace_id=request.trace_id,
                span_id=span_id
            )
    
    async def discover(self) -> List[AgentCapability]:
        """发现所有可用 Agent"""
        return self.registry.get_all_capabilities()


_global_registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """获取全局注册表"""
    return _global_registry


def create_mcp_client(db_session=None, user_context=None) -> LocalMCPClient:
    """创建 MCP 客户端"""
    return LocalMCPClient(_global_registry, db_session, user_context)
