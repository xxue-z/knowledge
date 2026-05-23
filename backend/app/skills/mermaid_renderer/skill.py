import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MermaidRendererSkill:
    """Mermaid 渲染 Skill - 生成思维导图和流程图"""

    def __init__(self):
        pass

    async def render(self, data: dict, format_type: str = "mermaid", depth: int = 3) -> dict:
        """渲染为指定格式"""
        if format_type == "mermaid":
            output = self._to_mermaid(data)
        elif format_type == "json":
            output = self._to_json(data)
        elif format_type == "markdown":
            output = self._to_markdown(data)
        else:
            output = self._to_mermaid(data)

        return {
            "output": output,
            "format": format_type,
            "node_count": self._count_nodes(output),
            "depth": depth
        }

    async def render_from_text(self, text: str, format_type: str = "mermaid", depth: int = 3) -> dict:
        """从文本生成思维导图"""
        topics = self._extract_topics(text)
        mindmap_data = {
            "name": text[:30] + ("..." if len(text) > 30 else ""),
            "children": [{"name": topic} for topic in topics]
        }
        return await self.render(mindmap_data, format_type, depth)

    def _to_mermaid(self, data: dict) -> str:
        """转换为 Mermaid 格式"""
        lines = ["mindmap"]
        self._build_mermaid(lines, data, 0)
        return "\n".join(lines)

    def _build_mermaid(self, lines: list, node: dict, level: int):
        """构建 Mermaid 格式"""
        name = node.get("name", "unnamed")
        indent = "  " * level

        if level == 0:
            lines.append(f'{indent}root(({name}))')
        else:
            lines.append(f'{indent}{name}')

        children = node.get("children", [])
        for child in children:
            self._build_mermaid(lines, child, level + 1)

    def _to_json(self, data: dict) -> str:
        """转换为 JSON 格式"""
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _to_markdown(self, data: dict) -> str:
        """转换为 Markdown 格式"""
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

    def _extract_topics(self, text: str) -> list:
        """从文本提取子主题"""
        default_topics = ["核心概念", "主要特点", "应用场景", "注意事项"]
        return default_topics[:3]

    def _count_nodes(self, text: str) -> int:
        """计算节点数量"""
        return text.count("[") if "[" in text else 5
