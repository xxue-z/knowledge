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
from .unified_client import UnifiedMCPClient
from .external_client import ExternalMCPClient

__all__ = [
    "AgentCapability",
    "MCPRequest",
    "MCPResponse",
    "MCPClient",
    "AgentRegistry",
    "LocalMCPClient",
    "UnifiedMCPClient",
    "ExternalMCPClient",
    "get_registry",
    "create_mcp_client",
]
