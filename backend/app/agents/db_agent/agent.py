import logging
from typing import Dict, Any

from app.mcps import AgentCapability, MCPRequest, MCPResponse, get_registry
from app.services.db_service import DBService
from app.models.schemas import UserContext
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DBAgent:
    """轻库 Agent - 员工档案数据库查询"""
    
    CAPABILITY = AgentCapability(
        agent_id="db_agent",
        name="轻库 Agent",
        description="员工档案数据库查询服务，支持员工信息查询、部门统计等",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get_employee_by_id", "get_employee_by_name", "get_employees_by_department", "count_by_department", "get_manager"]
                },
                "employee_id": {"type": "string"},
                "employee_name": {"type": "string"},
                "department": {"type": "string"},
                "dept_id": {"type": "string"}
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "employee_id": {"type": "string"},
                "name": {"type": "string"},
                "department": {"type": "string"},
                "level": {"type": "string"},
                "hire_date": {"type": "string"},
                "manager_id": {"type": "string"},
                "email": {"type": "string"},
                "status": {"type": "string"},
                "count": {"type": "integer"}
            }
        },
        supported_intents=["PURE_DB", "HYBRID"],
        version="1.0",
        priority=100
    )
    
    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user
        self.db_service = DBService(db, user)
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """处理 MCP 请求"""
        action = request.params.get("action")
        
        try:
            if action == "get_employee_by_id":
                employee_id = request.params.get("employee_id")
                employee = await self.db_service.get_employee_by_id(employee_id)
                if employee:
                    return MCPResponse(
                        success=True,
                        data={
                            "employee_id": employee.employee_id,
                            "name": employee.name,
                            "department": employee.department,
                            "level": employee.level,
                            "hire_date": str(employee.hire_date) if employee.hire_date else None,
                            "manager_id": employee.manager_id,
                            "email": employee.email,
                            "status": employee.status
                        },
                        sources=[{"type": "database", "table": "employees", "id": employee_id}],
                        confidence=1.0
                    )
                return MCPResponse(
                    success=False,
                    error=f"员工 {employee_id} 不存在",
                    confidence=0.0
                )
            
            elif action == "get_employee_by_name":
                name = request.params.get("employee_name")
                employee = await self.db_service.get_employee_by_name(name)
                if employee:
                    return MCPResponse(
                        success=True,
                        data={
                            "employee_id": employee.employee_id,
                            "name": employee.name,
                            "department": employee.department,
                            "level": employee.level,
                            "hire_date": str(employee.hire_date) if employee.hire_date else None,
                            "manager_id": employee.manager_id,
                            "email": employee.email,
                            "status": employee.status
                        },
                        sources=[{"type": "database", "table": "employees", "name": name}],
                        confidence=1.0
                    )
                return MCPResponse(
                    success=False,
                    error=f"员工 {name} 不存在",
                    confidence=0.0
                )
            
            elif action == "get_employees_by_department":
                department = request.params.get("department")
                employees = await self.db_service.get_employees_by_department(department)
                data = [{
                    "employee_id": emp.employee_id,
                    "name": emp.name,
                    "level": emp.level,
                    "status": emp.status
                } for emp in employees]
                return MCPResponse(
                    success=True,
                    data=data,
                    sources=[{"type": "database", "table": "employees", "filter": f"department={department}"}],
                    confidence=1.0
                )
            
            elif action == "count_by_department":
                department = request.params.get("department")
                count = await self.db_service.count_employees_by_department(department)
                return MCPResponse(
                    success=True,
                    data={"count": count, "department": department},
                    sources=[{"type": "database", "table": "employees", "filter": f"department={department}"}],
                    confidence=1.0
                )
            
            elif action == "get_manager":
                employee_id = request.params.get("employee_id")
                manager = await self.db_service.get_manager(employee_id)
                if manager:
                    return MCPResponse(
                        success=True,
                        data={
                            "employee_id": manager.employee_id,
                            "name": manager.name,
                            "department": manager.department,
                            "level": manager.level
                        },
                        sources=[{"type": "database", "table": "employees", "id": manager.employee_id}],
                        confidence=1.0
                    )
                return MCPResponse(
                    success=False,
                    error="未找到上级信息",
                    confidence=0.0
                )
            
            else:
                return MCPResponse(
                    success=False,
                    error=f"不支持的操作: {action}",
                    confidence=0.0
                )
        
        except Exception as e:
            logger.error(f"DBAgent error: {str(e)}")
            return MCPResponse(
                success=False,
                error=str(e),
                confidence=0.0
            )


def register_agent() -> None:
    """注册轻库 Agent - 注册类而不是实例"""
    registry = get_registry()
    registry.register(DBAgent.CAPABILITY, DBAgent)
