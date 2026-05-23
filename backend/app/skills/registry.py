"""Skill 注册表 - 管理所有可用 Skills"""

from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SkillCapability:
    """Skill 能力描述"""
    skill_id: str
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    supported_tasks: List[str]
    version: str = "1.0"
    priority: int = 100


class SkillRegistry:
    """Skill 注册表"""
    
    def __init__(self):
        self.skills: Dict[str, Dict[str, Any]] = {}
    
    def register(self, capability: SkillCapability, handler: Callable) -> None:
        """注册 Skill"""
        self.skills[capability.skill_id] = {
            "capability": capability,
            "handler": handler
        }
        logger.info(f"Skill registered: {capability.skill_id}")
    
    def unregister(self, skill_id: str) -> bool:
        """注销 Skill"""
        if skill_id in self.skills:
            del self.skills[skill_id]
            logger.info(f"Skill unregistered: {skill_id}")
            return True
        return False
    
    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取 Skill 信息"""
        return self.skills.get(skill_id)
    
    def find_by_task(self, task: str) -> List[Dict[str, Any]]:
        """根据任务类型查找支持的 Skill"""
        candidates = []
        for skill_id, info in self.skills.items():
            if task in info["capability"].supported_tasks:
                candidates.append(info)
        
        candidates.sort(key=lambda x: x["capability"].priority)
        return candidates
    
    def get_all_capabilities(self) -> List[SkillCapability]:
        """获取所有 Skill 能力描述"""
        return [info["capability"] for info in self.skills.values()]
    
    def is_registered(self, skill_id: str) -> bool:
        """检查 Skill 是否已注册"""
        return skill_id in self.skills


_global_skill_registry = SkillRegistry()


def get_skill_registry() -> SkillRegistry:
    """获取全局 Skill 注册表"""
    return _global_skill_registry
