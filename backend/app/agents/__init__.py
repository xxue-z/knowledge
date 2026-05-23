"""Agents - 各种专业 Agent 集合"""

from .db_agent import DBAgent, register_agent as register_db_agent
from .wiki_agent import WikiAgent, register_agent as register_wiki_agent
from .vector_agent import VectorAgent, register_agent as register_vector_agent
from .permission_agent import PermissionAgent, register_agent as register_permission_agent
from .content_analysis_agent import ContentAnalysisAgent, register_agent as register_content_analysis_agent
from .mindmap_agent import MindMapAgent, register_agent as register_mindmap_agent
from .coordinator import CoordinatorAgent
from .router import RouterAgent

__all__ = [
    "DBAgent",
    "WikiAgent",
    "VectorAgent",
    "PermissionAgent",
    "ContentAnalysisAgent",
    "MindMapAgent",
    "CoordinatorAgent",
    "RouterAgent",
    "register_db_agent",
    "register_wiki_agent",
    "register_vector_agent",
    "register_permission_agent",
    "register_content_analysis_agent",
    "register_mindmap_agent",
]
