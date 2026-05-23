import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.server.auth_server import AuthServer


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.get_by_username.return_value = None
    repo.create.return_value = MagicMock(id="user-id-123", username="testuser", roles=["user"], dept_id=None)
    return repo


class TestKeycloakAuthServer:
    @pytest.mark.asyncio
    async def test_keycloak_callback_new_user(self, mock_repo):
        server = AuthServer(mock_repo)
        result = await server.keycloak_callback("newuser")
        assert result["success"] is True
        assert "user_id" in result

    @pytest.mark.asyncio
    async def test_keycloak_callback_existing_user(self, mock_repo):
        mock_user = MagicMock(id="existing-user-id", username="existinguser", roles=["user"], dept_id="dept-1")
        mock_repo.get_by_username.return_value = mock_user
        
        server = AuthServer(mock_repo)
        result = await server.keycloak_callback("existinguser")
        assert result["success"] is True
        assert result["user_id"] == "existing-user-id"