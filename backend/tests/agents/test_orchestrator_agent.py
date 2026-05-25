import pytest
from unittest.mock import AsyncMock, patch
from app.agents.orchestrator import OrchestratorAgent
from app.models.schemas import UserContext

@pytest.mark.asyncio
async def test_classify_intent_db():
    user = UserContext(user_id="test", roles=["user"], dept_id="dept001")
    agent = OrchestratorAgent(db=None, user=user)

    result = await agent.classify_intent("查询员工张三的信息")
    assert result["intent"] == "PURE_DB"

@pytest.mark.asyncio
async def test_classify_intent_kb():
    user = UserContext(user_id="test", roles=["user"], dept_id="dept001")
    agent = OrchestratorAgent(db=None, user=user)

    result = await agent.classify_intent("查看考勤制度")
    assert result["intent"] == "PURE_KB"

@pytest.mark.asyncio
async def test_classify_intent_hybrid():
    user = UserContext(user_id="test", roles=["user"], dept_id="dept001")
    agent = OrchestratorAgent(db=None, user=user)

    result = await agent.classify_intent("查询员工张三的考勤记录和考勤制度")
    assert result["intent"] == "HYBRID"