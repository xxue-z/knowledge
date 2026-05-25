import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcps import AgentCapability, MCPRequest, MCPResponse, get_registry
from app.models.schemas import UserContext
from app.core.casbin_policy import check_permission
from app.skills import execute_skill

logger = logging.getLogger(__name__)


class SecurityAgent:
    """安全 Agent - 安全检查编排、RBAC权限检查"""

    CAPABILITY = AgentCapability(
        agent_id="security_agent",
        name="安全 Agent",
        description="安全检查服务，支持SQL注入检测、RBAC鉴权、敏感字段脱敏",
        input_schema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["check_sql_injection", "check_permission", "mask_sensitive", "get_permissions"]},
                "text": {"type": "string"},
                "resource": {"type": "string"},
                "action_type": {"type": "string"},
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
                "has_injection": {"type": "boolean"},
                "permissions": {"type": "array"}
            }
        },
        supported_intents=["PURE_DB", "PURE_KB", "HYBRID"],
        version="1.0",
        priority=10
    )

    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        action = request.params.get("action")

        try:
            if action == "check_sql_injection":
                text = request.params.get("text", "")
                result = await execute_skill("security_utils", "detect_sql_injection", {"text": text})
                return MCPResponse(
                    success=True,
                    data=result["data"],
                    sources=[{"type": "security", "action": "check_sql_injection"}],
                    confidence=1.0
                )

            elif action == "check_permission":
                resource = request.params.get("resource")
                action_type = request.params.get("action_type")
                allowed = await check_permission(self.user.roles, resource, action_type)
                return MCPResponse(
                    success=True,
                    data={"allowed": allowed},
                    sources=[{"type": "security", "action": "check_permission", "resource": resource}],
                    confidence=1.0
                )

            elif action == "mask_sensitive":
                data = request.params.get("data", {})
                resource_type = request.params.get("resource_type", "")
                result = await execute_skill("security_utils", "mask_sensitive_fields", {
                    "data": data,
                    "resource_type": resource_type
                })
                return MCPResponse(
                    success=True,
                    data={"data": result["data"]},
                    sources=[{"type": "security", "action": "mask_sensitive", "resource_type": resource_type}],
                    confidence=1.0
                )

            elif action == "get_permissions":
                permissions = []
                resources = ["wiki", "employee", "casbin_policy"]
                actions = ["read", "write", "delete", "manage"]
                for resource in resources:
                    for action_type in actions:
                        if await check_permission(self.user.roles, resource, action_type):
                            permissions.append({"resource": resource, "action": action_type})
                return MCPResponse(
                    success=True,
                    data={"permissions": permissions},
                    sources=[{"type": "security", "action": "get_permissions"}],
                    confidence=1.0
                )

            else:
                return MCPResponse(success=False, error=f"不支持的操作: {action}", confidence=0.0)

        except Exception as e:
            logger.error(f"SecurityAgent error: {str(e)}")
            return MCPResponse(success=False, error=str(e), confidence=0.0)


def register_agent() -> None:
    registry = get_registry()
    registry.register(SecurityAgent.CAPABILITY, SecurityAgent)