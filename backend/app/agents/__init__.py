"""Agents - 各种专业 Agent 集合"""

from .security import SecurityAgent, register_agent as register_security_agent
from .orchestrator import OrchestratorAgent, register_agent as register_orchestrator_agent
from .wiki_agent import WikiAgent, register_agent as register_wiki_agent
from .db_agent import DBAgent, register_agent as register_db_agent
from .vector_agent import VectorAgent, register_agent as register_vector_agent
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