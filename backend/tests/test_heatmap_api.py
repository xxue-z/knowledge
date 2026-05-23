import pytest
from unittest.mock import AsyncMock, MagicMock
from app.server.heatmap_server import HeatmapServer


@pytest.fixture
def mock_search_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_stats_repo():
    repo = AsyncMock()
    return repo


class TestHeatmapServer:
    @pytest.mark.asyncio
    async def test_record_search(self, mock_search_repo, mock_stats_repo):
        server = HeatmapServer(mock_search_repo, mock_stats_repo)
        await server.record_search("test-query", "user-123")
        mock_search_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_hot_queries(self, mock_search_repo, mock_stats_repo):
        server = HeatmapServer(mock_search_repo, mock_stats_repo)
        result = await server.get_hot_queries()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_hot_documents(self, mock_search_repo, mock_stats_repo):
        server = HeatmapServer(mock_search_repo, mock_stats_repo)
        result = await server.get_hot_documents()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_navigation_heat(self, mock_search_repo, mock_stats_repo):
        mock_stats_repo.get_by_type.return_value = []
        server = HeatmapServer(mock_search_repo, mock_stats_repo)
        result = await server.get_navigation_heat()
        assert isinstance(result, list)