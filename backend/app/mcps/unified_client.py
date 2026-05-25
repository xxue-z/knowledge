import logging
from typing import List, Dict, Any
from .mcp_protocol import AgentCapability, MCPRequest, MCPResponse, MCPClient
from .registry import get_registry, LocalMCPClient

logger = logging.getLogger(__name__)


class UnifiedMCPClient(MCPClient):
    """统一 MCP 客户端 - 支持内嵌和外源 MCP"""

    def __init__(self, db_session=None, user_context=None):
        self.local_client = LocalMCPClient(get_registry(), db_session, user_context)
        self.external_clients = {}

    def register_external_server(self, server_id: str, config: Dict[str, Any]):
        """注册外源 MCP Server"""
        from .external_client import ExternalMCPClient
        self.external_clients[server_id] = ExternalMCPClient(config)

    async def call(self, agent_or_server_id: str, request: MCPRequest) -> MCPResponse:
        """统一调用入口，自动区分内嵌/外源"""
        if agent_or_server_id in self.external_clients:
            logger.info(f"Calling external MCP server: {agent_or_server_id}")
            return await self.external_clients[agent_or_server_id].call(request)
        else:
            logger.info(f"Calling internal agent: {agent_or_server_id}")
            return await self.local_client.call(agent_or_server_id, request)

    async def discover(self) -> List[AgentCapability]:
        """发现所有可用 Agent（包含内嵌和外源）"""
        capabilities = await self.local_client.discover()
        for server_id, client in self.external_clients.items():
            try:
                external_caps = await client.list_tools()
                capabilities.extend(external_caps)
            except Exception as e:
                logger.error(f"Failed to discover external server {server_id}: {e}")
        return capabilities