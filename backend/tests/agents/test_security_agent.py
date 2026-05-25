import pytest
from unittest.mock import AsyncMock, patch
from app.agents.security import SecurityAgent
from app.models.schemas import UserContext
from app.mcps import MCPRequest

@pytest.mark.asyncio
async def test_check_sql_injection():
    user = UserContext(user_id="test", roles=["user"], dept_id="dept001")
    agent = SecurityAgent(db=None, user=user)

    request = MCPRequest(action="check_sql_injection", params={"text": "SELECT * FROM users"})
    response = await agent.handle_request(request)

    assert response.success is True
    assert "has_injection" in response.data

@pytest.mark.asyncio
async def test_check_sql_injection_safe():
    user = UserContext(user_id="test", roles=["user"], dept_id="dept001")
    agent = SecurityAgent(db=None, user=user)

    request = MCPRequest(action="check_sql_injection", params={"text": "查询员工信息"})
    response = await agent.handle_request(request)

    assert response.success is True
    assert response.data["has_injection"] is False

@pytest.mark.asyncio
async def test_mask_sensitive():
    user = UserContext(user_id="test", roles=["user"], dept_id="dept001")
    agent = SecurityAgent(db=None, user=user)

    request = MCPRequest(action="mask_sensitive", params={
        "data": {"name": "张三", "salary": 10000},
        "resource_type": "employees"
    })
    response = await agent.handle_request(request)

    assert response.success is True
    assert response.data["data"]["salary"] == "***"