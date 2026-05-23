import logging
import re

from app.mcps import AgentCapability, MCPRequest, MCPResponse, get_registry
from app.models.schemas import UserContext
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ContentAnalysisAgent:
    """内容分析 Agent - 敏感词检查、格式优化、自动分类"""
    
    CAPABILITY = AgentCapability(
        agent_id="content_analysis_agent",
        name="内容分析 Agent",
        description="内容分析服务，支持敏感词检查、格式优化、自动分类",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["check_sensitive", "format_text", "classify_content", "extract_keywords", "summarize"]
                },
                "text": {"type": "string"},
                "content_type": {"type": "string", "enum": ["wiki", "qa", "document"]}
            },
            "required": ["action", "text"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "has_sensitive": {"type": "boolean"},
                "sensitive_words": {"type": "array", "items": {"type": "string"}},
                "formatted_text": {"type": "string"},
                "category": {"type": "string"},
                "keywords": {"type": "array", "items": {"type": "string"}},
                "summary": {"type": "string"},
                "suggestions": {"type": "array", "items": {"type": "string"}}
            }
        },
        supported_intents=["PURE_KB", "HYBRID"],
        version="1.0",
        priority=100
    )
    
    SENSITIVE_WORDS = [
        "机密", "绝密", "保密", "内部资料",
        "密码", "密钥", "token", "api_key",
        "银行卡", "身份证", "手机号",
        "攻击", "漏洞", "入侵", "黑客"
    ]
    
    CATEGORIES = [
        {"name": "制度规范", "keywords": ["制度", "规定", "规范", "流程", "标准"]},
        {"name": "技术文档", "keywords": ["技术", "开发", "API", "代码", "架构"]},
        {"name": "人事信息", "keywords": ["员工", "入职", "离职", "绩效", "考勤"]},
        {"name": "财务相关", "keywords": ["报销", "费用", "薪酬", "工资", "预算"]},
        {"name": "项目管理", "keywords": ["项目", "任务", "进度", "里程碑"]},
        {"name": "会议纪要", "keywords": ["会议", "纪要", "记录", "决议"]},
        {"name": "常见问题", "keywords": ["FAQ", "问题", "解答", "如何", "怎么"]},
        {"name": "其他", "keywords": []}
    ]
    
    def __init__(self, db_session, user: UserContext):
        self.user = user
        self.llm = LLMService()
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """处理 MCP 请求"""
        action = request.params.get("action")
        text = request.params.get("text", "")
        
        try:
            if action == "check_sensitive":
                sensitive_words = self._detect_sensitive(text)
                return MCPResponse(
                    success=True,
                    data={
                        "has_sensitive": len(sensitive_words) > 0,
                        "sensitive_words": sensitive_words,
                        "suggestions": self._generate_suggestions(sensitive_words)
                    },
                    sources=[{"type": "content_analysis", "action": "check_sensitive"}],
                    confidence=1.0
                )
            
            elif action == "format_text":
                formatted = self._format_text(text)
                return MCPResponse(
                    success=True,
                    data={"formatted_text": formatted},
                    sources=[{"type": "content_analysis", "action": "format_text"}],
                    confidence=0.9
                )
            
            elif action == "classify_content":
                category = self._classify_text(text)
                return MCPResponse(
                    success=True,
                    data={"category": category},
                    sources=[{"type": "content_analysis", "action": "classify_content"}],
                    confidence=0.8
                )
            
            elif action == "extract_keywords":
                keywords = self._extract_keywords(text)
                return MCPResponse(
                    success=True,
                    data={"keywords": keywords},
                    sources=[{"type": "content_analysis", "action": "extract_keywords"}],
                    confidence=0.85
                )
            
            elif action == "summarize":
                summary = await self._summarize_text(text)
                return MCPResponse(
                    success=True,
                    data={"summary": summary},
                    sources=[{"type": "content_analysis", "action": "summarize"}],
                    confidence=0.8
                )
            
            else:
                return MCPResponse(
                    success=False,
                    error=f"不支持的操作: {action}",
                    confidence=0.0
                )
        
        except Exception as e:
            logger.error(f"ContentAnalysisAgent error: {str(e)}")
            return MCPResponse(
                success=False,
                error=str(e),
                confidence=0.0
            )
    
    def _detect_sensitive(self, text: str) -> list:
        """检测敏感词"""
        found = []
        for word in self.SENSITIVE_WORDS:
            if word in text:
                found.append(word)
        return found
    
    def _generate_suggestions(self, sensitive_words: list) -> list:
        """生成修改建议"""
        suggestions = []
        if sensitive_words:
            suggestions.append(f"检测到 {len(sensitive_words)} 个敏感词: {', '.join(sensitive_words)}")
            suggestions.append("建议：请检查内容是否包含敏感信息，并考虑脱敏处理")
        return suggestions
    
    def _format_text(self, text: str) -> str:
        """格式化文本"""
        text = text.strip()
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text
    
    def _classify_text(self, text: str) -> str:
        """分类文本"""
        scores = []
        for category in self.CATEGORIES:
            score = sum(1 for kw in category["keywords"] if kw in text)
            scores.append((category["name"], score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[0][0] if scores[0][1] > 0 else "其他"
    
    def _extract_keywords(self, text: str) -> list:
        """提取关键词"""
        all_keywords = set()
        for category in self.CATEGORIES:
            for kw in category["keywords"]:
                if kw in text:
                    all_keywords.add(kw)
        return list(all_keywords)[:10]
    
    async def _summarize_text(self, text: str) -> str:
        """总结文本"""
        if len(text) <= 100:
            return text
        
        try:
            summary = await self.llm.summarize(text)
            return summary
        except Exception:
            return text[:200] + "..."


def register_agent() -> None:
    """注册内容分析 Agent - 注册类而不是实例"""
    registry = get_registry()
    registry.register(ContentAnalysisAgent.CAPABILITY, ContentAnalysisAgent)
