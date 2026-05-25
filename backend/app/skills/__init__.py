"""Skills - 可复用的技能模块集合"""

from .registry import SkillRegistry, SkillCapability, get_skill_registry
from .init import register_all_skills, execute_skill, get_skill_handler

__all__ = [
    "SkillRegistry",
    "SkillCapability",
    "get_skill_registry",
    "register_all_skills",
    "execute_skill",
    "get_skill_handler",
]


def get_security_utils():
    """延迟导入 SecurityUtilsSkill"""
    from .security_utils import SecurityUtilsSkill, execute
    return SecurityUtilsSkill, execute


def get_content_classifier():
    """延迟导入 ContentClassifierSkill"""
    from .content_classifier import ContentClassifierSkill, execute
    return ContentClassifierSkill, execute


def get_mermaid_renderer():
    """延迟导入 MermaidRendererSkill"""
    from .mermaid_renderer import MermaidRendererSkill, execute
    return MermaidRendererSkill, execute


def get_intent_classifier():
    """延迟导入 IntentClassifierSkill"""
    from .intent_classifier import IntentClassifierSkill, execute
    return IntentClassifierSkill, execute
