import pytest
from unittest.mock import AsyncMock
from app.mcps import UnifiedMCPClient, MCPRequest

@pytest.mark.asyncio
async def test_unified_client():
    client = UnifiedMCPClient()
    request = MCPRequest(action="test", params={})

    result = await client.call("unknown_agent", request)
    assert result.success is False

@pytest.mark.asyncio
async def test_register_external_server():
    client = UnifiedMCPClient()
    client.register_external_server("test_server", {"server_url": "http://localhost:8000"})
    
    assert "test_server" in client.external_clients