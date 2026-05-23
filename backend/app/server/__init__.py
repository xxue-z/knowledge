from functools import lru_cache
from fastapi import Depends
from app.dal import get_adapter
from app.dal.repositories import (
    WikiPageRepository,
    WikiPageVersionRepository,
    LocalUserRepository,
    KnowledgeNavRepository,
    NavContentLinkRepository,
    SearchEventRepository,
    HeatmapStatsRepository,
    AuditLogRepository,
)
from .wiki_server import WikiServer
from .auth_server import AuthServer
from .knowledge_server import KnowledgeServer
from .heatmap_server import HeatmapServer
from .admin_server import AdminServer
from .qa_server import QAServer

@lru_cache()
def get_wiki_page_repo() -> WikiPageRepository:
    adapter = get_adapter()
    return WikiPageRepository(adapter)

@lru_cache()
def get_wiki_version_repo() -> WikiPageVersionRepository:
    adapter = get_adapter()
    return WikiPageVersionRepository(adapter)

def get_wiki_server(
    page_repo: WikiPageRepository = Depends(get_wiki_page_repo),
    version_repo: WikiPageVersionRepository = Depends(get_wiki_version_repo),
) -> WikiServer:
    return WikiServer(page_repo, version_repo)

@lru_cache()
def get_local_user_repo() -> LocalUserRepository:
    adapter = get_adapter()
    return LocalUserRepository(adapter)

def get_auth_server(
    user_repo: LocalUserRepository = Depends(get_local_user_repo),
) -> AuthServer:
    return AuthServer(user_repo)

@lru_cache()
def get_knowledge_nav_repo() -> KnowledgeNavRepository:
    adapter = get_adapter()
    return KnowledgeNavRepository(adapter)

@lru_cache()
def get_nav_content_link_repo() -> NavContentLinkRepository:
    adapter = get_adapter()
    return NavContentLinkRepository(adapter)

def get_knowledge_server(
    nav_repo: KnowledgeNavRepository = Depends(get_knowledge_nav_repo),
    link_repo: NavContentLinkRepository = Depends(get_nav_content_link_repo),
) -> KnowledgeServer:
    return KnowledgeServer(nav_repo, link_repo)

@lru_cache()
def get_search_event_repo() -> SearchEventRepository:
    adapter = get_adapter()
    return SearchEventRepository(adapter)

@lru_cache()
def get_heatmap_stats_repo() -> HeatmapStatsRepository:
    adapter = get_adapter()
    return HeatmapStatsRepository(adapter)

def get_heatmap_server(
    search_event_repo: SearchEventRepository = Depends(get_search_event_repo),
    stats_repo: HeatmapStatsRepository = Depends(get_heatmap_stats_repo),
) -> HeatmapServer:
    return HeatmapServer(search_event_repo, stats_repo)

@lru_cache()
def get_audit_log_repo() -> AuditLogRepository:
    adapter = get_adapter()
    return AuditLogRepository(adapter)

def get_admin_server(
    audit_log_repo: AuditLogRepository = Depends(get_audit_log_repo),
) -> AdminServer:
    return AdminServer(audit_log_repo)

def get_qa_server() -> QAServer:
    return QAServer()

__all__ = [
    "WikiServer",
    "get_wiki_server",
    "get_wiki_page_repo",
    "get_wiki_version_repo",
    "AuthServer",
    "get_auth_server",
    "get_local_user_repo",
    "KnowledgeServer",
    "get_knowledge_server",
    "get_knowledge_nav_repo",
    "get_nav_content_link_repo",
    "HeatmapServer",
    "get_heatmap_server",
    "get_search_event_repo",
    "get_heatmap_stats_repo",
    "AdminServer",
    "get_admin_server",
    "get_audit_log_repo",
    "QAServer",
    "get_qa_server",
]
