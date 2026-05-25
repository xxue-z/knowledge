import logging
import httpx
from typing import List, Dict, Any
from .mcp_protocol import MCPRequest, MCPResponse, MCPClient

logger = logging.getLogger(__name__)


class ExternalMCPClient(MCPClient):
    """外源 MCP 客户端（标准协议）"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.url = config.get("server_url")
        self.api_key = config.get("api_key")

    async def call(self, request: MCPRequest) -> MCPResponse:
        """调用标准 MCP Server"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                payload = {
                    "action": request.action,
                    "params": request.params,
                    "context": request.context
                }

                response = await client.post(
                    f"{self.url}/mcp/call",
                    json=payload,
                    headers=headers,
                    timeout=30
                )

                data = response.json()
                return MCPResponse(
                    success=data.get("success", False),
                    data=data.get("data"),
                    error=data.get("error"),
                    confidence=data.get("confidence", 0.0)
                )
        except Exception as e:
            logger.error(f"External MCP call failed: {e}")
            return MCPResponse(success=False, error=str(e), confidence=0.0)

    async def list_tools(self) -> List[dict]:
        """列出所有工具"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                response = await client.get(f"{self.url}/mcp/list_tools", headers=headers)
                return response.json()
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []

    async def discover(self) -> List[dict]:
        return await self.list_tools()