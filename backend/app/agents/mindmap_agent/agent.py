import logging
import json

from app.mcps import AgentCapability, MCPRequest, MCPResponse, get_registry
from app.models.schemas import UserContext
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class MindMapAgent:
    """思维导图 Agent - 知识整合与可视化"""
    
    CAPABILITY = AgentCapability(
        agent_id="mindmap_agent",
        name="思维导图 Agent",
        description="知识整合与思维导图生成服务，支持 JSON 和 Mermaid 格式输出",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["generate", "convert", "simplify", "expand"]
                },
                "data": {"type": "object"},
                "text": {"type": "string"},
                "format": {"type": "string", "enum": ["json", "mermaid", "markdown"]},
                "depth": {"type": "integer", "minimum": 1, "maximum": 5}
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "mindmap": {"type": "string"},
                "format": {"type": "string"},
                "nodes": {"type": "integer"},
                "depth": {"type": "integer"}
            }
        },
        supported_intents=["PURE_KB", "HYBRID"],
        version="1.0",
        priority=100
    )
    
    def __init__(self, db_session, user: UserContext):
        self.user = user
        self.llm = LLMService()
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """处理 MCP 请求"""
        action = request.params.get("action")
        format_type = request.params.get("format", "json")
        depth = request.params.get("depth", 3)
        
        try:
            if action == "generate":
                text = request.params.get("text", "")
                mindmap = await self._generate_mindmap(text, format_type, depth)
                
                return MCPResponse(
                    success=True,
                    data={
                        "mindmap": mindmap,
                        "format": format_type,
                        "nodes": self._count_nodes(mindmap),
                        "depth": depth
                    },
                    sources=[{"type": "mindmap", "action": "generate"}],
                    confidence=0.85
                )
            
            elif action == "convert":
                data = request.params.get("data", {})
                mindmap = self._convert_to_format(data, format_type)
                
                return MCPResponse(
                    success=True,
                    data={
                        "mindmap": mindmap,
                        "format": format_type,
                        "nodes": self._count_nodes(mindmap),
                        "depth": depth
                    },
                    sources=[{"type": "mindmap", "action": "convert"}],
                    confidence=0.95
                )
            
            elif action == "simplify":
                data = request.params.get("data", {})
                simplified = self._simplify_mindmap(data, depth)
                
                return MCPResponse(
                    success=True,
                    data={
                        "mindmap": self._convert_to_format(simplified, format_type),
                        "format": format_type,
                        "nodes": len(simplified.get("children", [])) + 1,
                        "depth": depth
                    },
                    sources=[{"type": "mindmap", "action": "simplify"}],
                    confidence=0.9
                )
            
            elif action == "expand":
                data = request.params.get("data", {})
                expanded = await self._expand_mindmap(data, depth)
                
                return MCPResponse(
                    success=True,
                    data={
                        "mindmap": self._convert_to_format(expanded, format_type),
                        "format": format_type,
                        "nodes": self._count_nodes_from_json(expanded),
                        "depth": depth
                    },
                    sources=[{"type": "mindmap", "action": "expand"}],
                    confidence=0.8
                )
            
            else:
                return MCPResponse(
                    success=False,
                    error=f"不支持的操作: {action}",
                    confidence=0.0
                )
        
        except Exception as e:
            logger.error(f"MindMapAgent error: {str(e)}")
            return MCPResponse(
                success=False,
                error=str(e),
                confidence=0.0
            )
    
    async def _generate_mindmap(self, text: str, format_type: str, depth: int) -> str:
        """生成思维导图"""
        if not text:
            return ""
        
        try:
            return await self.llm.generate_mindmap(text, format_type, depth)
        except Exception:
            return self._fallback_mindmap(text, format_type, depth)
    
    def _fallback_mindmap(self, text: str, format_type: str, depth: int) -> str:
        """降级思维导图生成"""
        topics = ["核心主题", "子主题1", "子主题2", "子主题3"]
        
        if format_type == "mermaid":
            nodes = "\n".join([f"    {i+1}[{topic}]" for i, topic in enumerate(topics)])
            edges = "\n".join([f"    0 --> {i+1}" for i in range(len(topics))])
            return f"mindmap\n  root(({text[:20]}...))\n{nodes}\n{edges}"
        elif format_type == "markdown":
            return f"# {text[:30]}...\n\n- 子主题1\n- 子主题2\n- 子主题3"
        else:
            return json.dumps({
                "name": text[:30] + "...",
                "children": [{"name": t} for t in topics]
            }, ensure_ascii=False)
    
    def _convert_to_format(self, data: dict, format_type: str) -> str:
        """转换为指定格式"""
        if format_type == "json":
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif format_type == "mermaid":
            return self._json_to_mermaid(data)
        elif format_type == "markdown":
            return self._json_to_markdown(data)
        return json.dumps(data, ensure_ascii=False)
    
    def _json_to_mermaid(self, data: dict) -> str:
        """JSON 转 Mermaid"""
        lines = ["mindmap"]
        self._build_mermaid(lines, data, "root", 0)
        return "\n".join(lines)
    
    def _build_mermaid(self, lines: list, node: dict, parent: str, level: int):
        """构建 Mermaid 格式"""
        name = node.get("name", "unnamed")
        indent = "  " * level
        
        if level == 0:
            lines.append(f'{indent}root(({name}))')
        else:
            lines.append(f'{indent}{name}')
        
        children = node.get("children", [])
        for child in children:
            self._build_mermaid(lines, child, name, level + 1)
    
    def _json_to_markdown(self, data: dict) -> str:
        """JSON 转 Markdown"""
        lines = []
        self._build_markdown(lines, data, 0)
        return "\n".join(lines)
    
    def _build_markdown(self, lines: list, node: dict, level: int):
        """构建 Markdown 格式"""
        name = node.get("name", "unnamed")
        prefix = "#" * (level + 1)
        
        lines.append(f'{prefix} {name}')
        
        children = node.get("children", [])
        for child in children:
            self._build_markdown(lines, child, level + 1)
    
    def _simplify_mindmap(self, data: dict, max_depth: int) -> dict:
        """简化思维导图"""
        simplified = {"name": data.get("name", "")}
        
        if max_depth > 1:
            children = data.get("children", [])[:3]
            simplified["children"] = [
                self._simplify_mindmap(child, max_depth - 1)
                for child in children
            ]
        
        return simplified
    
    async def _expand_mindmap(self, data: dict, depth: int) -> dict:
        """扩展思维导图"""
        expanded = {"name": data.get("name", "")}
        expanded["children"] = data.get("children", [])
        
        if depth > len(expanded["children"]):
            for i in range(len(expanded["children"]), depth):
                expanded["children"].append({"name": f"子主题{i+1}"})
        
        return expanded
    
    def _count_nodes(self, text: str) -> int:
        """计算节点数量"""
        return text.count("[") if "[" in text else 5
    
    def _count_nodes_from_json(self, data: dict) -> int:
        """从 JSON 计算节点数量"""
        count = 1
        children = data.get("children", [])
        for child in children:
            count += self._count_nodes_from_json(child)
        return count


def register_agent() -> None:
    """注册思维导图 Agent - 注册类而不是实例"""
    registry = get_registry()
    registry.register(MindMapAgent.CAPABILITY, MindMapAgent)
