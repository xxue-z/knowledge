import pytest
from app.skills import execute_skill

@pytest.mark.asyncio
async def test_execute_security_utils():
    result = await execute_skill("security_utils", "detect_sql_injection", {"text": "SELECT * FROM users WHERE id=1 OR 1=1"})
    assert result["success"] is True
    assert result["data"]["has_injection"] is True

@pytest.mark.asyncio
async def test_execute_content_classifier():
    result = await execute_skill("content_classifier", "classify", {"text": "员工考勤制度"})
    assert result["success"] is True
    assert result["data"]["category"] == "人事信息"

@pytest.mark.asyncio
async def test_execute_skill_not_found():
    result = await execute_skill("unknown_skill", "action", {})
    assert result["success"] is False

@pytest.mark.asyncio
async def test_execute_format_text():
    result = await execute_skill("content_classifier", "format_text", {"text": "  有很多  空格  "})
    assert result["success"] is True
    assert "  " not in result["data"]["formatted_text"]