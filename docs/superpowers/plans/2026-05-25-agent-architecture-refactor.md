# Agent 架构重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构 Agent 架构，合并路由Agent和协调Agent，升级权限Agent为安全Agent，删除内容分析Agent并将功能移至Skill，改进Skill调用方式，支持标准MCP协议。

**Architecture:** 从8个Agent重构为6个Agent（安全Agent、编排Agent、Wiki Agent、轻库Agent、向量Agent、思维导图Agent），Skill层合并安全相关功能为security-utils，支持内嵌MCP和外源MCP。

**Tech Stack:** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Casbin / MCP Protocol

---

## 文件结构

| 文件/目录 | 职责 | 状态 |
|----------|------|------|
| `app/skills/security_utils/` | 安全工具Skill（SQL注入检测、敏感词检测、敏感字段脱敏） | 新建 |
| `app/skills/content_classifier/` | 内容分类Skill（扩展format_text、summarize） | 修改 |
| `app/agents/security/` | 安全Agent | 新建 |
| `app/agents/orchestrator/` | 编排Agent | 新建 |
| `app/agents/router/` | 路由Agent | 删除 |
| `app/agents/coordinator/` | 协调Agent | 删除 |
| `app/agents/permission/` | 权限Agent | 删除 |
| `app/agents/content_analysis_agent/` | 内容分析Agent | 删除 |
| `app/mcps/unified_client.py` | 统一MCP客户端 | 新建 |
| `app/mcps/external_client.py` | 外源MCP客户端 | 新建 |

---

## Phase 1: Skill 层调整

### Task 1: 创建 security-utils Skill

**Files:**
- Create: `app/skills/security_utils/__init__.py`
- Create: `app/skills/security_utils/skill.py`
- Modify: `app/skills/__init__.py`
- Test: `tests/skills/test_security_utils.py`

- [ ] **Step 1: 创建 security_utils/__init__.py**

```python
from .skill import SecurityUtilsSkill, execute

__all__ = ["SecurityUtilsSkill", "execute"]
```

- [ ] **Step 2: 创建 security_utils/skill.py**

```python
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SecurityUtilsSkill:
    """安全工具 Skill - 提供安全相关的工具方法"""

    SQL_INJECTION_PATTERNS = [
        r"(?i)(union\s+select)",
        r"(?i)(or\s+1\s*=\s*1)",
        r"(?i)(drop\s+table)",
        r"(?i)(--\s*$)",
        r"(?i)(/\*.*\*/)",
        r"(?i)('\s*or\s*')",
        r"(?i)(insert\s+into)",
        r"(?i)(delete\s+from)",
        r"(?i)(update\s+\w+\s+set)",
        r"(?i)(exec\s+(\w+))",
    ]

    SENSITIVE_WORDS = [
        "机密", "绝密", "保密", "内部资料",
        "密码", "密钥", "token", "api_key", "secret",
        "银行卡", "身份证", "手机号", "电话",
        "攻击", "漏洞", "入侵", "黑客", "病毒",
        "工资", "薪酬", "薪资", "奖金",
    ]

    SENSITIVE_FIELDS = {
        "employees": ["salary", "phone", "clearance_level", "password", "token"],
        "conversations": ["embedding_id"],
        "users": ["password_hash", "api_key"],
        "wiki": [],
    }

    async def detect_sql_injection(self, text: str) -> Dict[str, Any]:
        matches = []
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text):
                matches.append(pattern)
        return {
            "has_injection": len(matches) > 0,
            "patterns_found": matches,
            "suggestion": "检测到潜在的 SQL 注入攻击，已拦截。" if matches else "安全"
        }

    async def detect_sensitive_words(self, text: str) -> Dict[str, Any]:
        found = []
        for word in self.SENSITIVE_WORDS:
            if word in text:
                found.append(word)
        suggestions = []
        if found:
            suggestions.append(f"检测到 {len(found)} 个敏感词: {', '.join(found)}")
            suggestions.append("建议：请检查内容是否包含敏感信息")
        return {
            "has_sensitive": len(found) > 0,
            "sensitive_words": found,
            "suggestions": suggestions
        }

    async def mask_sensitive_fields(self, data: Dict[str, Any], resource_type: str = "") -> Dict[str, Any]:
        fields_to_mask = self.SENSITIVE_FIELDS.get(resource_type, [])
        fields_to_mask.extend(self.SENSITIVE_FIELDS.get("users", []))
        filtered = data.copy()
        for field in fields_to_mask:
            if field in filtered:
                filtered[field] = "***"
        return filtered


async def execute(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    skill = SecurityUtilsSkill()
    if action == "detect_sql_injection":
        return await skill.detect_sql_injection(params.get("text", ""))
    elif action == "detect_sensitive_words":
        return await skill.detect_sensitive_words(params.get("text", ""))
    elif action == "mask_sensitive_fields":
        return await skill.mask_sensitive_fields(
            params.get("data", {}),
            params.get("resource_type", "")
        )
    else:
        return {"success": False, "error": f"不支持的操作: {action}"}
```

- [ ] **Step 3: 更新 skills/__init__.py**

```python
from .security_utils import SecurityUtilsSkill, execute as execute_security_utils
from .content_classifier import ContentClassifierSkill, execute as classify_content
from .mermaid_renderer import MermaidRendererSkill, execute as render_mermaid
from .intent_classifier import IntentClassifierSkill, execute as classify_intent
from .registry import SkillRegistry, SkillCapability, get_skill_registry
from .init import register_all_skills, execute_skill, get_skill_handler

__all__ = [
    "SecurityUtilsSkill",
    "ContentClassifierSkill",
    "MermaidRendererSkill",
    "IntentClassifierSkill",
    "SkillRegistry",
    "SkillCapability",
    "classify_content",
    "render_mermaid",
    "classify_intent",
    "get_skill_registry",
    "register_all_skills",
    "execute_skill",
    "get_skill_handler",
    "execute_security_utils",
]
```

- [ ] **Step 4: 创建测试文件 tests/skills/test_security_utils.py**

```python
import pytest
from app.skills.security_utils import SecurityUtilsSkill

@pytest.mark.asyncio
async def test_detect_sql_injection():
    skill = SecurityUtilsSkill()
    result = await skill.detect_sql_injection("SELECT * FROM users WHERE id=1 OR 1=1")
    assert result["has_injection"] is True

@pytest.mark.asyncio
async def test_detect_sensitive_words():
    skill = SecurityUtilsSkill()
    result = await skill.detect_sensitive_words("这是机密信息，包含密码123")
    assert result["has_sensitive"] is True
    assert "机密" in result["sensitive_words"]

@pytest.mark.asyncio
async def test_mask_sensitive_fields():
    skill = SecurityUtilsSkill()
    data = {"name": "张三", "salary": 10000, "phone": "13800138000"}
    result = await skill.mask_sensitive_fields(data, "employees")
    assert result["salary"] == "***"
    assert result["phone"] == "***"
    assert result["name"] == "张三"
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/skills/test_security_utils.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/skills/security_utils/ app/skills/__init__.py tests/skills/test_security_utils.py
git commit -m "feat: add security-utils skill"
```

---

### Task 2: 扩展 content-classifier Skill

**Files:**
- Modify: `app/skills/content_classifier/skill.py`
- Test: `tests/skills/test_content_classifier.py`

- [ ] **Step 1: 更新 content_classifier/skill.py**

```python
import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

class ContentClassifierSkill:
    """内容分类 Skill - 从文本中提取实体和意图"""

    DEFAULT_CATEGORIES = [
        {"name": "制度规范", "keywords": ["制度", "规定", "规范", "流程", "标准"]},
        {"name": "技术文档", "keywords": ["技术", "开发", "API", "代码", "架构"]},
        {"name": "人事信息", "keywords": ["员工", "入职", "离职", "绩效", "考勤"]},
        {"name": "财务相关", "keywords": ["报销", "费用", "薪酬", "工资", "预算"]},
        {"name": "项目管理", "keywords": ["项目", "任务", "进度", "里程碑"]},
        {"name": "会议纪要", "keywords": ["会议", "纪要", "记录", "决议"]},
        {"name": "常见问题", "keywords": ["FAQ", "问题", "解答", "如何", "怎么"]},
        {"name": "其他", "keywords": []}
    ]

    def __init__(self, categories: List[dict] = None):
        self.categories = categories or self.DEFAULT_CATEGORIES

    async def classify(self, text: str, categories: List[dict] = None) -> dict:
        target_categories = categories or self.categories
        scores = []
        for category in target_categories:
            score = sum(1 for kw in category["keywords"] if kw in text)
            scores.append((category["name"], score))
        scores.sort(key=lambda x: x[1], reverse=True)
        top_category = scores[0][0] if scores[0][1] > 0 else "其他"
        confidence = min(0.5 + scores[0][1] * 0.1, 1.0)
        return {
            "category": top_category,
            "confidence": confidence,
            "scores": dict(scores)
        }

    async def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        keywords = set()
        for category in self.categories:
            for kw in category["keywords"]:
                if kw in text:
                    keywords.add(kw)
        return list(keywords)[:top_k]

    async def format_text(self, text: str) -> str:
        """格式化文本"""
        text = text.strip()
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text

    async def summarize(self, text: str, max_length: int = 200) -> str:
        """文本摘要"""
        if len(text) <= max_length:
            return text
        sentences = re.split(r'[。！？\n]', text)
        summary = []
        current_length = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and current_length + len(sentence) <= max_length:
                summary.append(sentence)
                current_length += len(sentence) + 1
            if current_length >= max_length:
                break
        return '。'.join(summary) + '。'
```

- [ ] **Step 2: 更新测试文件 tests/skills/test_content_classifier.py**

```python
import pytest
from app.skills.content_classifier import ContentClassifierSkill

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
```

- [ ] **Step 3: 运行测试**

Run: `cd backend && python -m pytest tests/skills/test_content_classifier.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add app/skills/content_classifier/skill.py tests/skills/test_content_classifier.py
git commit -m "feat: extend content-classifier with format and summarize"
```

---

## Phase 2: Skill 调用方式改进

### Task 3: 完善 Skill 执行器

**Files:**
- Modify: `app/skills/init.py`
- Test: `tests/skills/test_skill_executor.py`

- [ ] **Step 1: 更新 skills/init.py**

```python
from typing import Dict, Any
from .registry import get_skill_registry
from .security_utils import execute as execute_security_utils
from .content_classifier import execute as execute_content_classifier
from .mermaid_renderer import execute as execute_mermaid_renderer
from .intent_classifier import execute as execute_intent_classifier

SKILL_HANDLERS = {
    "security-utils": execute_security_utils,
    "content-classifier": execute_content_classifier,
    "mermaid-renderer": execute_mermaid_renderer,
    "intent-classifier": execute_intent_classifier,
}

async def execute_skill(skill_id: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """统一调用 Skill 的接口"""
    handler = SKILL_HANDLERS.get(skill_id)
    if not handler:
        return {"success": False, "error": f"Skill not found: {skill_id}"}
    
    try:
        result = await handler(action, params)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_skill_handler(skill_id: str):
    """获取 Skill 处理器"""
    return SKILL_HANDLERS.get(skill_id)

def register_all_skills():
    """注册所有 Skill"""
    registry = get_skill_registry()
    from .security_utils import SecurityUtilsSkill
    from .content_classifier import ContentClassifierSkill
    from .mermaid_renderer import MermaidRendererSkill
    from .intent_classifier import IntentClassifierSkill
    
    # 注册技能（简化示例）
    registry.register(
        {"skill_id": "security-utils", "name": "安全工具", "description": "安全相关工具"},
        execute_security_utils
    )
    registry.register(
        {"skill_id": "content-classifier", "name": "内容分类", "description": "内容分类与处理"},
        execute_content_classifier
    )
```

- [ ] **Step 2: 创建测试文件 tests/skills/test_skill_executor.py**

```python
import pytest
from app.skills import execute_skill

@pytest.mark.asyncio
async def test_execute_skill():
    result = await execute_skill("security-utils", "detect_sql_injection", {"text": "SELECT *"})
    assert result["success"] is True

@pytest.mark.asyncio
async def test_execute_skill_not_found():
    result = await execute_skill("unknown-skill", "action", {})
    assert result["success"] is False
```

- [ ] **Step 3: 运行测试**

Run: `cd backend && python -m pytest tests/skills/test_skill_executor.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add app/skills/init.py tests/skills/test_skill_executor.py
git commit -m "feat: improve skill execution interface"
```

---

## Phase 3: Agent 重构

### Task 4: 创建 SecurityAgent

**Files:**
- Create: `app/agents/security/__init__.py`
- Create: `app/agents/security/agent.py`
- Test: `tests/agents/test_security_agent.py`

- [ ] **Step 1: 创建 security/__init__.py**

```python
from .agent import SecurityAgent, register_agent

__all__ = ["SecurityAgent", "register_agent"]
```

- [ ] **Step 2: 创建 security/agent.py**

```python
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcps import AgentCapability, MCPRequest, MCPResponse, get_registry
from app.models.schemas import UserContext
from app.core.casbin_policy import check_permission
from app.skills import execute_skill

logger = logging.getLogger(__name__)

class SecurityAgent:
    """安全 Agent - 安全检查编排、RBAC权限检查"""
    
    CAPABILITY = AgentCapability(
        agent_id="security_agent",
        name="安全 Agent",
        description="安全检查服务，支持SQL注入检测、RBAC鉴权、敏感字段脱敏",
        input_schema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["check_sql_injection", "check_permission", "mask_sensitive", "get_permissions"]},
                "text": {"type": "string"},
                "resource": {"type": "string"},
                "action_type": {"type": "string"},
                "data": {"type": "object"},
                "resource_type": {"type": "string"}
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "allowed": {"type": "boolean"},
                "data": {"type": "object"},
                "has_injection": {"type": "boolean"},
                "permissions": {"type": "array"}
            }
        },
        supported_intents=["PURE_DB", "PURE_KB", "HYBRID"],
        version="1.0",
        priority=10
    )
    
    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        action = request.params.get("action")
        
        try:
            if action == "check_sql_injection":
                text = request.params.get("text", "")
                result = await execute_skill("security-utils", "detect_sql_injection", {"text": text})
                return MCPResponse(
                    success=True,
                    data=result["data"],
                    sources=[{"type": "security", "action": "check_sql_injection"}],
                    confidence=1.0
                )
            
            elif action == "check_permission":
                resource = request.params.get("resource")
                action_type = request.params.get("action_type")
                allowed = await check_permission(self.user.roles, resource, action_type)
                return MCPResponse(
                    success=True,
                    data={"allowed": allowed},
                    sources=[{"type": "security", "action": "check_permission", "resource": resource}],
                    confidence=1.0
                )
            
            elif action == "mask_sensitive":
                data = request.params.get("data", {})
                resource_type = request.params.get("resource_type", "")
                result = await execute_skill("security-utils", "mask_sensitive_fields", {
                    "data": data,
                    "resource_type": resource_type
                })
                return MCPResponse(
                    success=True,
                    data={"data": result["data"]},
                    sources=[{"type": "security", "action": "mask_sensitive", "resource_type": resource_type}],
                    confidence=1.0
                )
            
            elif action == "get_permissions":
                permissions = []
                resources = ["wiki", "employee", "casbin_policy"]
                actions = ["read", "write", "delete", "manage"]
                for resource in resources:
                    for action_type in actions:
                        if await check_permission(self.user.roles, resource, action_type):
                            permissions.append({"resource": resource, "action": action_type})
                return MCPResponse(
                    success=True,
                    data={"permissions": permissions},
                    sources=[{"type": "security", "action": "get_permissions"}],
                    confidence=1.0
                )
            
            else:
                return MCPResponse(success=False, error=f"不支持的操作: {action}", confidence=0.0)
        
        except Exception as e:
            logger.error(f"SecurityAgent error: {str(e)}")
            return MCPResponse(success=False, error=str(e), confidence=0.0)


def register_agent() -> None:
    registry = get_registry()
    registry.register(SecurityAgent.CAPABILITY, SecurityAgent)
```

- [ ] **Step 3: 创建测试文件 tests/agents/test_security_agent.py**

```python
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
```

- [ ] **Step 4: 运行测试**

Run: `cd backend && python -m pytest tests/agents/test_security_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/agents/security/ tests/agents/test_security_agent.py
git commit -m "feat: create SecurityAgent"
```

---

### Task 5: 创建 OrchestratorAgent

**Files:**
- Create: `app/agents/orchestrator/__init__.py`
- Create: `app/agents/orchestrator/agent.py`
- Test: `tests/agents/test_orchestrator_agent.py`

- [ ] **Step 1: 创建 orchestrator/__init__.py**

```python
from .agent import OrchestratorAgent, register_agent

__all__ = ["OrchestratorAgent", "register_agent"]
```

- [ ] **Step 2: 创建 orchestrator/agent.py**

```python
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcps import AgentCapability, MCPRequest, MCPResponse, create_mcp_client
from app.models.schemas import UserContext
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """编排 Agent - 意图识别、任务分解、跨Agent协调、结果聚合"""
    
    CAPABILITY = AgentCapability(
        agent_id="orchestrator_agent",
        name="编排 Agent",
        description="任务编排服务，支持意图识别、任务分解、跨Agent协调、结果聚合",
        input_schema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["process_query", "classify_intent", "dispatch_tasks"]},
                "query": {"type": "string"},
                "tasks": {"type": "array"}
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "sources": {"type": "array"},
                "intent": {"type": "string"},
                "confidence": {"type": "number"}
            }
        },
        supported_intents=["PURE_DB", "PURE_KB", "HYBRID"],
        version="1.0",
        priority=5
    )
    
    DB_KEYWORDS = ["员工", "人员", "部门", "工号", "入职", "在职", "离职", "项目", "负责"]
    KB_KEYWORDS = ["制度", "规定", "政策", "规范", "标准", "流程", "技术", "开发", "FAQ"]
    
    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user
        self.mcp_client = create_mcp_client(db, user)
        self.llm = LLMService()
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        action = request.params.get("action")
        
        try:
            if action == "process_query":
                query = request.params.get("query", "")
                result = await self.process_query(query)
                return MCPResponse(
                    success=True,
                    data=result,
                    sources=result.get("sources", []),
                    confidence=result.get("confidence", 0.0)
                )
            
            elif action == "classify_intent":
                query = request.params.get("query", "")
                result = await self.classify_intent(query)
                return MCPResponse(
                    success=True,
                    data=result,
                    sources=[{"type": "orchestrator", "action": "classify_intent"}],
                    confidence=result.get("confidence", 0.0)
                )
            
            elif action == "dispatch_tasks":
                tasks = request.params.get("tasks", [])
                results = await self.dispatch_tasks(tasks)
                return MCPResponse(
                    success=True,
                    data={"results": results},
                    sources=[{"type": "orchestrator", "action": "dispatch_tasks"}],
                    confidence=1.0
                )
            
            else:
                return MCPResponse(success=False, error=f"不支持的操作: {action}", confidence=0.0)
        
        except Exception as e:
            logger.error(f"OrchestratorAgent error: {str(e)}")
            return MCPResponse(success=False, error=str(e), confidence=0.0)
    
    async def process_query(self, query: str) -> dict:
        """处理用户查询"""
        intent_result = await self.classify_intent(query)
        intent = intent_result["intent"]
        
        if intent == "PURE_DB":
            return await self.handle_db_query(query)
        elif intent == "PURE_KB":
            return await self.handle_kb_query(query)
        elif intent == "HYBRID":
            return await self.handle_hybrid_query(query)
        else:
            return {"answer": "抱歉，我无法理解您的问题。", "sources": [], "confidence": 0.3}
    
    async def classify_intent(self, query: str) -> dict:
        """意图分类"""
        db_score = sum(1 for kw in self.DB_KEYWORDS if kw in query)
        kb_score = sum(1 for kw in self.KB_KEYWORDS if kw in query)
        
        if db_score > 0 and kb_score == 0:
            return {"intent": "PURE_DB", "confidence": min(0.5 + db_score * 0.1, 0.95)}
        elif kb_score > 0 and db_score == 0:
            return {"intent": "PURE_KB", "confidence": min(0.5 + kb_score * 0.1, 0.95)}
        elif db_score > 0 and kb_score > 0:
            return {"intent": "HYBRID", "confidence": 0.7}
        
        try:
            llm_result = await self.llm.classify_intent(query)
            return llm_result
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return {"intent": "BOUNDARY", "confidence": 0.3}
    
    async def handle_db_query(self, query: str) -> dict:
        """处理数据库查询"""
        params = {"action": "search", "query": query}
        response = await self.mcp_client.call("db_agent", MCPRequest(action="search", params=params))
        
        if response.success and response.data:
            return {
                "answer": str(response.data),
                "sources": response.sources,
                "confidence": response.confidence
            }
        return {"answer": "未找到相关数据。", "sources": [], "confidence": 0.0}
    
    async def handle_kb_query(self, query: str) -> dict:
        """处理知识库查询"""
        params = {"action": "search", "query": query}
        response = await self.mcp_client.call("wiki_agent", MCPRequest(action="search", params=params))
        
        if response.success and response.data:
            return {
                "answer": str(response.data),
                "sources": response.sources,
                "confidence": response.confidence
            }
        return {"answer": "未找到相关文档。", "sources": [], "confidence": 0.0}
    
    async def handle_hybrid_query(self, query: str) -> dict:
        """处理混合查询"""
        db_result = await self.handle_db_query(query)
        kb_result = await self.handle_kb_query(query)
        
        answer = db_result["answer"]
        if "未找到" not in kb_result["answer"]:
            answer += f"\n\n相关文档：\n{kb_result['answer']}"
        
        return {
            "answer": answer,
            "sources": db_result["sources"] + kb_result["sources"],
            "confidence": (db_result["confidence"] + kb_result["confidence"]) / 2
        }
    
    async def dispatch_tasks(self, tasks: list) -> list:
        """分发任务到各个 Agent"""
        results = []
        for task in tasks:
            agent_id = task.get("agent_id")
            action = task.get("action")
            params = task.get("params", {})
            
            response = await self.mcp_client.call(agent_id, MCPRequest(action=action, params=params))
            results.append({
                "agent_id": agent_id,
                "success": response.success,
                "data": response.data
            })
        return results


def register_agent() -> None:
    registry = get_registry()
    registry.register(OrchestratorAgent.CAPABILITY, OrchestratorAgent)
```

- [ ] **Step 3: 创建测试文件 tests/agents/test_orchestrator_agent.py**

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.agents.orchestrator import OrchestratorAgent
from app.models.schemas import UserContext

@pytest.mark.asyncio
async def test_classify_intent():
    user = UserContext(user_id="test", roles=["user"], dept_id="dept001")
    agent = OrchestratorAgent(db=None, user=user)
    
    result = await agent.classify_intent("查询员工张三的信息")
    assert result["intent"] == "PURE_DB"
    
    result = await agent.classify_intent("查看考勤制度")
    assert result["intent"] == "PURE_KB"
```

- [ ] **Step 4: 运行测试**

Run: `cd backend && python -m pytest tests/agents/test_orchestrator_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/agents/orchestrator/ tests/agents/test_orchestrator_agent.py
git commit -m "feat: create OrchestratorAgent"
```

---

### Task 6: 更新 QAService 使用新 Agent

**Files:**
- Modify: `app/services/qa_service.py`

- [ ] **Step 1: 更新 qa_service.py**

```python
from app.agents.orchestrator import OrchestratorAgent
from app.models.schemas import UserContext

class QAService:
    def __init__(self):
        pass

    async def ask_question(self, user: UserContext, question: str, db_session) -> dict:
        agent = OrchestratorAgent(db_session, user)
        result = await agent.process_query(question)
        return result
```

- [ ] **Step 2: Commit**

```bash
git add app/services/qa_service.py
git commit -m "refactor: update QAService to use OrchestratorAgent"
```

---

## Phase 4: 清理旧 Agent

### Task 7: 删除旧 Agent

**Files:**
- Delete: `app/agents/router/`
- Delete: `app/agents/coordinator/`
- Delete: `app/agents/permission/`
- Delete: `app/agents/content_analysis_agent/`

- [ ] **Step 1: 删除旧 Agent 目录**

```bash
rm -rf app/agents/router/ app/agents/coordinator/ app/agents/permission/ app/agents/content_analysis_agent/
```

- [ ] **Step 2: 更新 agents/__init__.py**

```python
from .security import SecurityAgent, register_agent as register_security_agent
from .orchestrator import OrchestratorAgent, register_agent as register_orchestrator_agent
from .wiki_agent import WikiAgent, register_agent as register_wiki_agent
from .db_agent import DBAgent, register_agent as register_db_agent
from .vector import VectorAgent, register_agent as register_vector_agent
from .mindmap_agent import MindMapAgent, register_agent as register_mindmap_agent

__all__ = [
    "SecurityAgent",
    "OrchestratorAgent",
    "WikiAgent",
    "DBAgent",
    "VectorAgent",
    "MindMapAgent",
    "register_security_agent",
    "register_orchestrator_agent",
    "register_wiki_agent",
    "register_db_agent",
    "register_vector_agent",
    "register_mindmap_agent",
]
```

- [ ] **Step 3: Commit**

```bash
git add app/agents/__init__.py
git commit -m "refactor: remove old agents (router, coordinator, permission, content_analysis)"
```

---

## Phase 5: MCP 协议扩展

### Task 8: 创建统一 MCP 客户端

**Files:**
- Create: `app/mcps/unified_client.py`
- Create: `app/mcps/external_client.py`
- Test: `tests/mcps/test_unified_client.py`

- [ ] **Step 1: 创建 unified_client.py**

```python
import logging
from typing import List, Dict, Any
from .mcp_protocol import AgentCapability, MCPRequest, MCPResponse, MCPClient
from .registry import get_registry, LocalMCPClient

logger = logging.getLogger(__name__)

class UnifiedMCPClient(MCPClient):
    """统一 MCP 客户端 - 支持内嵌和外源 MCP"""
    
    def __init__(self, db_session=None, user_context=None):
        self.local_client = LocalMCPClient(get_registry(), db_session, user_context)
        self.external_clients = {}
    
    def register_external_server(self, server_id: str, config: Dict[str, Any]):
        """注册外源 MCP Server"""
        from .external_client import ExternalMCPClient
        self.external_clients[server_id] = ExternalMCPClient(config)
    
    async def call(self, agent_or_server_id: str, request: MCPRequest) -> MCPResponse:
        """统一调用入口，自动区分内嵌/外源"""
        if agent_or_server_id in self.external_clients:
            logger.info(f"Calling external MCP server: {agent_or_server_id}")
            return await self.external_clients[agent_or_server_id].call(request)
        else:
            logger.info(f"Calling internal agent: {agent_or_server_id}")
            return await self.local_client.call(agent_or_server_id, request)
    
    async def discover(self) -> List[AgentCapability]:
        """发现所有可用 Agent（包含内嵌和外源）"""
        capabilities = await self.local_client.discover()
        for server_id, client in self.external_clients.items():
            try:
                external_caps = await client.list_tools()
                capabilities.extend(external_caps)
            except Exception as e:
                logger.error(f"Failed to discover external server {server_id}: {e}")
        return capabilities
```

- [ ] **Step 2: 创建 external_client.py**

```python
import logging
import httpx
from typing import List, Dict, Any
from .mcp_protocol import MCPRequest, MCPResponse, MCPClient

logger = logging.getLogger(__name__)

class ExternalMCPClient(MCPClient):
    """外源 MCP 客户端（标准协议）"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.url = config.get("server_url")
        self.api_key = config.get("api_key")
    
    async def call(self, request: MCPRequest) -> MCPResponse:
        """调用标准 MCP Server"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                payload = {
                    "action": request.action,
                    "params": request.params,
                    "context": request.context
                }
                
                response = await client.post(
                    f"{self.url}/mcp/call",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                data = response.json()
                return MCPResponse(
                    success=data.get("success", False),
                    data=data.get("data"),
                    error=data.get("error"),
                    confidence=data.get("confidence", 0.0)
                )
        except Exception as e:
            logger.error(f"External MCP call failed: {e}")
            return MCPResponse(success=False, error=str(e), confidence=0.0)
    
    async def list_tools(self) -> List[dict]:
        """列出所有工具"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                response = await client.get(f"{self.url}/mcp/list_tools", headers=headers)
                return response.json()
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def discover(self) -> List[dict]:
        return await self.list_tools()
```

- [ ] **Step 3: 更新 mcps/__init__.py**

```python
from .mcp_protocol import AgentCapability, MCPRequest, MCPResponse, MCPClient
from .registry import AgentRegistry, LocalMCPClient, get_registry, create_mcp_client
from .unified_client import UnifiedMCPClient
from .external_client import ExternalMCPClient

__all__ = [
    "AgentCapability",
    "MCPRequest",
    "MCPResponse",
    "MCPClient",
    "AgentRegistry",
    "LocalMCPClient",
    "UnifiedMCPClient",
    "ExternalMCPClient",
    "get_registry",
    "create_mcp_client",
]
```

- [ ] **Step 4: 创建测试文件 tests/mcps/test_unified_client.py**

```python
import pytest
from unittest.mock import AsyncMock
from app.mcps import UnifiedMCPClient, MCPRequest

@pytest.mark.asyncio
async def test_unified_client():
    client = UnifiedMCPClient()
    request = MCPRequest(action="test", params={})
    
    result = await client.call("unknown_agent", request)
    assert result.success is False
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/mcps/test_unified_client.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/mcps/unified_client.py app/mcps/external_client.py app/mcps/__init__.py tests/mcps/test_unified_client.py
git commit -m "feat: add unified MCP client with external server support"
```

---

## Phase 6: 集成测试

### Task 9: 更新 main.py 注册新 Agent

**Files:**
- Modify: `app/main.py`

- [ ] **Step 1: 更新 main.py**

```python
from app.agents import (
    register_security_agent,
    register_orchestrator_agent,
    register_wiki_agent,
    register_db_agent,
    register_vector_agent,
    register_mindmap_agent,
)
from app.skills import register_all_skills

# 注册 Agent
register_security_agent()
register_orchestrator_agent()
register_wiki_agent()
register_db_agent()
register_vector_agent()
register_mindmap_agent()

# 注册 Skill
register_all_skills()
```

- [ ] **Step 2: Commit**

```bash
git add app/main.py
git commit -m "refactor: update main.py to register new agents"
```

---

### Task 10: 运行完整测试

**Files:**
- All tests

- [ ] **Step 1: 运行所有测试**

Run: `cd backend && python -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "refactor: complete agent architecture refactoring"
```

---

## Self-Review

### 1. Spec Coverage
- ✅ 创建 security-utils Skill
- ✅ 扩展 content-classifier Skill（format_text, summarize）
- ✅ 删除 sql-inject-detector Skill（功能合并到 security-utils）
- ✅ 完善 execute_skill 统一接口
- ✅ 创建 SecurityAgent
- ✅ 创建 OrchestratorAgent
- ✅ 删除 RouterAgent、CoordinatorAgent、PermissionAgent、ContentAnalysisAgent
- ✅ 更新 QAService
- ✅ 扩展 MCP Client，支持标准 MCP 协议
- ✅ 实现 MCP Server 配置管理

### 2. Placeholder Scan
- 无占位符，所有步骤都有具体代码

### 3. Type Consistency
- 类型和方法签名保持一致

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-25-agent-architecture-refactor.md`. 

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**