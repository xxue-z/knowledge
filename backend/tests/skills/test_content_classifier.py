import pytest
from app.skills.content_classifier import ContentClassifierSkill

@pytest.mark.asyncio
async def test_classify():
    skill = ContentClassifierSkill()
    result = await skill.classify("员工考勤制度")
    assert result["category"] == "人事信息"

@pytest.mark.asyncio
async def test_extract_keywords():
    skill = ContentClassifierSkill()
    result = await skill.extract_keywords("技术文档开发指南")
    assert "技术" in result
    assert "开发" in result

@pytest.mark.asyncio
async def test_detect_sensitive():
    skill = ContentClassifierSkill()
    result = await skill.detect_sensitive("包含机密信息")
    assert result["has_sensitive"] is True

@pytest.mark.asyncio
async def test_format_text():
    skill = ContentClassifierSkill()
    text = "  这是一段  有很多   空格的文本\n\n\n\n还有空行\n"
    result = await skill.format_text(text)
    assert "  " not in result
    assert "\n\n\n" not in result

@pytest.mark.asyncio
async def test_summarize():
    skill = ContentClassifierSkill()
    text = "这是一段很长的文本，用于测试摘要功能。" * 20
    result = await skill.summarize(text, max_length=50)
    assert len(result) <= 50

@pytest.mark.asyncio
async def test_summarize_short():
    skill = ContentClassifierSkill()
    text = "短文本"
    result = await skill.summarize(text, max_length=50)
    assert result == text