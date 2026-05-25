import pytest
from app.skills.security_utils import SecurityUtilsSkill

@pytest.mark.asyncio
async def test_detect_sql_injection():
    skill = SecurityUtilsSkill()
    result = await skill.detect_sql_injection("SELECT * FROM users WHERE id=1 OR 1=1")
    assert result["has_injection"] is True

@pytest.mark.asyncio
async def test_detect_sql_injection_safe():
    skill = SecurityUtilsSkill()
    result = await skill.detect_sql_injection("查询用户信息")
    assert result["has_injection"] is False

@pytest.mark.asyncio
async def test_detect_sensitive_words():
    skill = SecurityUtilsSkill()
    result = await skill.detect_sensitive_words("这是机密信息，包含密码123")
    assert result["has_sensitive"] is True
    assert "机密" in result["sensitive_words"]
    assert "密码" in result["sensitive_words"]

@pytest.mark.asyncio
async def test_detect_sensitive_words_none():
    skill = SecurityUtilsSkill()
    result = await skill.detect_sensitive_words("普通文本内容")
    assert result["has_sensitive"] is False

@pytest.mark.asyncio
async def test_mask_sensitive_fields():
    skill = SecurityUtilsSkill()
    data = {"name": "张三", "salary": 10000, "phone": "13800138000"}
    result = await skill.mask_sensitive_fields(data, "employees")
    assert result["salary"] == "***"
    assert result["phone"] == "***"
    assert result["name"] == "张三"

@pytest.mark.asyncio
async def test_mask_sensitive_fields_empty():
    skill = SecurityUtilsSkill()
    data = {"name": "张三"}
    result = await skill.mask_sensitive_fields(data, "wiki")
    assert result == data