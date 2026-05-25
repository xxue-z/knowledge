"""Content Classifier Skill - 内容分类"""

from .skill import ContentClassifierSkill

__all__ = ["ContentClassifierSkill", "execute"]


async def execute(text: str, categories: list = None) -> dict:
    """执行内容分类"""
    skill = ContentClassifierSkill()
    return await skill.classify(text, categories)
