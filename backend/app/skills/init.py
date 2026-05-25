"""Skills 初始化 - 注册所有可用 Skills"""

import logging
from typing import Any, Dict

from app.skills.registry import SkillCapability, get_skill_registry

logger = logging.getLogger(__name__)

SKILL_HANDLERS = {}


def _register_content_classifier():
    """注册内容分类 Skill"""
    from app.skills.content_classifier import ContentClassifierSkill
    
    capability = SkillCapability(
        skill_id="content_classifier",
        name="内容分类器",
        description="对文本进行分类、提取关键词、检测敏感词、格式化、摘要",
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "action": {"type": "string", "enum": ["classify", "extract_keywords", "detect_sensitive", "format_text", "summarize"]},
                "categories": {"type": "array"},
                "max_length": {"type": "integer"}
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
                "sensitive_words": {"type": "array"},
                "formatted_text": {"type": "string"},
                "summary": {"type": "string"}
            }
        },
        supported_tasks=["content_classification", "keyword_extraction", "sensitive_detection", "text_formatting", "text_summarization"],
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
        elif action == "format_text":
            return {"formatted_text": await skill.format_text(params["text"])}
        elif action == "summarize":
            return {"summary": await skill.summarize(params["text"], params.get("max_length", 200))}
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


def _register_security_utils():
    """注册安全工具 Skill"""
    from app.skills.security_utils import SecurityUtilsSkill
    
    capability = SkillCapability(
        skill_id="security_utils",
        name="安全工具",
        description="SQL注入检测、敏感词检测、敏感字段脱敏",
        input_schema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["detect_sql_injection", "detect_sensitive_words", "mask_sensitive_fields"]},
                "text": {"type": "string"},
                "data": {"type": "object"},
                "resource_type": {"type": "string"}
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "has_injection": {"type": "boolean"},
                "has_sensitive": {"type": "boolean"},
                "patterns_found": {"type": "array"},
                "sensitive_words": {"type": "array"},
                "data": {"type": "object"}
            }
        },
        supported_tasks=["sql_injection_detection", "sensitive_word_detection", "data_masking"],
        version="1.0",
        priority=50
    )
    
    async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
        skill = SecurityUtilsSkill()
        action = params.get("action")
        
        if action == "detect_sql_injection":
            return await skill.detect_sql_injection(params.get("text", ""))
        elif action == "detect_sensitive_words":
            return await skill.detect_sensitive_words(params.get("text", ""))
        elif action == "mask_sensitive_fields":
            return {"data": await skill.mask_sensitive_fields(
                params.get("data", {}),
                params.get("resource_type", "")
            )}
        else:
            return {"error": f"Unknown action: {action}"}
    
    registry = get_skill_registry()
    registry.register(capability, handler)


def register_all_skills() -> None:
    """注册所有 Skills"""
    _register_content_classifier()
    _register_mermaid_renderer()
    _register_intent_classifier()
    _register_security_utils()
    
    registry = get_skill_registry()
    logger.info(f"All skills registered: {len(registry.skills)} skills available")


def get_skill_handler(skill_id: str):
    """获取 Skill 的处理函数"""
    registry = get_skill_registry()
    skill_info = registry.get_skill(skill_id)
    if skill_info:
        return skill_info["handler"]
    return None


async def execute_skill(skill_id: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """统一调用 Skill 的接口"""
    handler = get_skill_handler(skill_id)
    if not handler:
        return {"success": False, "error": f"Skill not found: {skill_id}"}
    
    try:
        params_with_action = params.copy()
        params_with_action["action"] = action
        result = await handler(params_with_action)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
