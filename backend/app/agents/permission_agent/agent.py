import logging

from app.mcps import AgentCapability, MCPRequest, MCPResponse, get_registry
from app.models.schemas import UserContext
from app.core.casbin_policy import check_permission

logger = logging.getLogger(__name__)


class PermissionAgent:
    """权限 Agent - 权限检查和敏感字段脱敏"""
    
    CAPABILITY = AgentCapability(
        agent_id="permission_agent",
        name="权限 Agent",
        description="权限检查和敏感字段脱敏服务",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["check_access", "filter_sensitive", "get_permissions", "get_accessible_scopes"]
                },
                "resource": {"type": "string"},
                "action_type": {"type": "string"},
                "scope": {"type": "string"},
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
                "permissions": {"type": "array"},
                "scopes": {"type": "array"}
            }
        },
        supported_intents=["PURE_DB", "PURE_KB", "HYBRID"],
        version="1.0",
        priority=50
    )
    
    def __init__(self, db_session, user: UserContext):
        self.user = user
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """处理 MCP 请求"""
        action = request.params.get("action")
        
        try:
            if action == "check_access":
                resource = request.params.get("resource")
                action_type = request.params.get("action_type")
                scope = request.params.get("scope", "all")
                
                allowed = await check_permission(self.user.roles, resource, action_type)
                return MCPResponse(
                    success=True,
                    data={"allowed": allowed},
                    sources=[{"type": "permission", "action": "check_access", "resource": resource}],
                    confidence=1.0
                )
            
            elif action == "filter_sensitive":
                data = request.params.get("data", {})
                resource_type = request.params.get("resource_type", "")
                
                filtered_data = await self._filter_sensitive_fields(data, resource_type)
                return MCPResponse(
                    success=True,
                    data={"data": filtered_data},
                    sources=[{"type": "permission", "action": "filter_sensitive", "resource_type": resource_type}],
                    confidence=1.0
                )
            
            elif action == "get_permissions":
                permissions = []
                resources = ["wiki", "employee", "casbin_policy"]
                actions = ["read", "write", "delete", "manage"]
                
                for resource in resources:
                    for action_type in actions:
                        if await check_permission(self.user.roles, resource, action_type):
                            permissions.append({
                                "resource": resource,
                                "action": action_type
                            })
                
                return MCPResponse(
                    success=True,
                    data={"permissions": permissions},
                    sources=[{"type": "permission", "action": "get_permissions"}],
                    confidence=1.0
                )
            
            elif action == "get_accessible_scopes":
                resource = request.params.get("resource")
                action_type = request.params.get("action_type")
                
                scopes = []
                for scope in ["own", "department", "all"]:
                    if await check_permission(self.user.roles, resource, action_type):
                        scopes.append(scope)
                
                return MCPResponse(
                    success=True,
                    data={"scopes": scopes},
                    sources=[{"type": "permission", "action": "get_accessible_scopes"}],
                    confidence=1.0
                )
            
            else:
                return MCPResponse(
                    success=False,
                    error=f"不支持的操作: {action}",
                    confidence=0.0
                )
        
        except Exception as e:
            logger.error(f"PermissionAgent error: {str(e)}")
            return MCPResponse(
                success=False,
                error=str(e),
                confidence=0.0
            )
    
    async def _filter_sensitive_fields(self, data: dict, resource_type: str) -> dict:
        """根据权限过滤敏感字段"""
        sensitive_fields = {
            "employees": ["salary", "phone", "clearance_level"],
            "conversations": ["embedding_id"],
            "wiki": []
        }
        
        fields_to_mask = sensitive_fields.get(resource_type, [])
        
        if "hr" in self.user.roles or "admin" in self.user.roles:
            return data
        
        filtered = data.copy()
        for field in fields_to_mask:
            if field in filtered:
                filtered[field] = "***"
        return filtered


def register_agent() -> None:
    """注册权限 Agent - 注册类而不是实例"""
    registry = get_registry()
    registry.register(PermissionAgent.CAPABILITY, PermissionAgent)
