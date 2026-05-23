"""MCP (Model Context Protocol) - Agent 通信协议"""

from .mcp_protocol import (
    AgentCapability,
    MCPRequest,
    MCPResponse,
    MCPClient,
)
from .registry import (
    AgentRegistry,
    LocalMCPClient,
    get_registry,
    create_mcp_client,
)

__all__ = [
    "AgentCapability",
    "MCPRequest",
    "MCPResponse",
    "MCPClient",
    "AgentRegistry",
    "LocalMCPClient",
    "get_registry",
    "create_mcp_client",
]
