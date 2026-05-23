"""Skills 初始化 - 注册所有可用 Skills"""

import logging
from typing import Any, Dict

from app.skills.registry import SkillCapability, get_skill_registry

logger = logging.getLogger(__name__)


def _register_content_classifier():
    """注册内容分类 Skill"""
    from app.skills.content_classifier import ContentClassifierSkill
    
    capability = SkillCapability(
        skill_id="content_classifier",
        name="内容分类器",
        description="对文本进行分类、提取关键词、检测敏感词",
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "action": {"type": "string", "enum": ["classify", "extract_keywords", "detect_sensitive"]},
                "categories": {"type": "array"}
            },
            "required": ["text", "action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "confidence": {"type": "number"},
                "keywords": {"type": "array"},
                "has_sensitive": {"type": "boolean"},
                "sensitive_words": {"type": "array"}
            }
        },
        supported_tasks=["content_classification", "keyword_extraction", "sensitive_detection"],
        version="1.0",
        priority=100
    )
    
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        skill = ContentClassifierSkill()
        action = params.get("action", "classify")
        
        if action == "classify":
            return await skill.classify(params["text"], params.get("categories"))
        elif action == "extract_keywords":
            return {"keywords": await skill.extract_keywords(params["text"])}
        elif action == "detect_sensitive":
            return await skill.detect_sensitive(params["text"])
        else:
            return {"error": f"Unknown action: {action}"}
    
    registry = get_skill_registry()
    registry.register(capability, handler)


def _register_mermaid_renderer():
    """注册思维导图渲染 Skill"""
    from app.skills.mermaid_renderer import MermaidRendererSkill
    
    capability = SkillCapability(
        skill_id="mermaid_renderer",
        name="Mermaid 渲染器",
        description="将数据渲染为思维导图或流程图，支持 Mermaid/JSON/Markdown 格式",
        input_schema={
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "format": {"type": "string", "enum": ["mermaid", "json", "markdown"]},
                "depth": {"type": "integer", "minimum": 1, "maximum": 5}
            },
            "required": ["data"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "output": {"type": "string"},
                "format": {"type": "string"},
                "node_count": {"type": "integer"},
                "depth": {"type": "integer"}
            }
        },
        supported_tasks=["mindmap_generation", "diagram_rendering", "format_conversion"],
        version="1.0",
        priority=100
    )
    
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        skill = MermaidRendererSkill()
        return await skill.render(
            params["data"],
            params.get("format", "mermaid"),
            params.get("depth", 3)
        )
    
    registry = get_skill_registry()
    registry.register(capability, handler)


def _register_intent_classifier():
    """注册意图分类 Skill"""
    from app.skills.intent_classifier import IntentClassifierSkill
    
    capability = SkillCapability(
        skill_id="intent_classifier",
        name="意图分类器",
        description="判断用户查询的意图（数据库查询/知识库查询/混合查询）",
        input_schema={
            "type": "object",
            "properties": {
                "question": {"type": "string"}
            },
            "required": ["question"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "intent": {"type": "string", "enum": ["PURE_DB", "PURE_KB", "HYBRID", "BOUNDARY", "SECURITY_BLOCK"]},
                "confidence": {"type": "number"},
                "entities": {"type": "object"},
                "keywords": {"type": "array"}
            }
        },
        supported_tasks=["intent_classification", "entity_extraction", "sql_injection_detection"],
        version="1.0",
        priority=50
    )
    
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        skill = IntentClassifierSkill()
        return await skill.classify(params["question"])
    
    registry = get_skill_registry()
    registry.register(capability, handler)


def register_all_skills() -> None:
    """注册所有 Skills"""
    _register_content_classifier()
    _register_mermaid_renderer()
    _register_intent_classifier()
    
    registry = get_skill_registry()
    logger.info(f"All skills registered: {len(registry.skills)} skills available")


def get_skill_handler(skill_id: str):
    """获取 Skill 的处理函数"""
    registry = get_skill_registry()
    skill_info = registry.get_skill(skill_id)
    if skill_info:
        return skill_info["handler"]
    return None


async def execute_skill(skill_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """执行指定的 Skill"""
    handler = get_skill_handler(skill_id)
    if handler:
        return await handler(params)
    return {"error": f"Skill not found: {skill_id}"}
