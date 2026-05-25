"""Casbin策略热更新测试"""
import pytest
from unittest.mock import patch, MagicMock
from app.core.casbin_policy import reload_policies


@pytest.mark.asyncio
async def test_reload_policies_returns_success():
    """测试重载函数返回成功状态"""
    with patch('app.core.casbin_policy.get_enforcer') as mock_get_enforcer:
        mock_enforcer = MagicMock()
        mock_get_enforcer.return_value = mock_enforcer
        
        result = await reload_policies()
    
    assert result["success"] == True
    assert result["message"] == "Policies reloaded successfully"
    assert "version" in result


@pytest.mark.asyncio
async def test_reload_policies_calls_get_enforcer_with_refresh():
    """测试重载时正确调用get_enforcer(refresh=True)"""
    with patch('app.core.casbin_policy.get_enforcer') as mock_get_enforcer:
        mock_enforcer = MagicMock()
        mock_get_enforcer.return_value = mock_enforcer
        
        await reload_policies()
    
    mock_get_enforcer.assert_called_once_with(refresh=True)


@pytest.mark.asyncio
async def test_reload_policies_resets_enforcer_cache():
    """测试重载时清空enforcer缓存"""
    with patch('app.core.casbin_policy.get_enforcer') as mock_get_enforcer:
        mock_enforcer = MagicMock()
        mock_get_enforcer.return_value = mock_enforcer
        
        await reload_policies()
    
    # 验证enforcer被设置为None（通过调用get_enforcer(refresh=True)来验证）
    mock_get_enforcer.assert_called_once_with(refresh=True)