from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import PlainTextResponse

from app.core.security import get_current_active_user
from app.models.schemas import UserContext, AuditLogResponse, PolicyCreate, RoleAssign
from app.services import get_admin_service, AdminService

router = APIRouter()


@router.get("/audit-logs")
async def get_audit_logs(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """
    查询审计日志列表
    
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    - **user_id**: 用户ID
    - **action**: 操作类型
    - **page**: 页码
    - **page_size**: 每页数量
    """
    if "admin" not in current_user.roles and "audit" not in current_user.roles:
        raise HTTPException(status_code=403, detail="无审计权限")
    
    return await service.query_audit_logs(
        start_time=start_time,
        end_time=end_time,
        user_id=user_id,
        action=action,
        page=page,
        page_size=page_size
    )


@router.get("/audit-logs/{log_id}")
async def get_audit_log_detail(
    log_id: int,
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """获取审计日志详情"""
    if "admin" not in current_user.roles and "audit" not in current_user.roles:
        raise HTTPException(status_code=403, detail="无审计权限")
    
    log = await service.get_audit_log_detail(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    return log


@router.get("/audit-logs/export")
async def export_audit_logs(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """导出审计日志为CSV"""
    if "admin" not in current_user.roles and "audit" not in current_user.roles:
        raise HTTPException(status_code=403, detail="无审计权限")
    
    csv_content = await service.export_audit_logs(
        start_time=start_time,
        end_time=end_time,
        user_id=user_id,
        action=action
    )
    
    return PlainTextResponse(
        content=csv_content,
        headers={
            "Content-Disposition": 'attachment; filename="audit_logs.csv"',
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


@router.get("/users")
async def list_users(
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await service.list_users(current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/permissions")
async def get_permissions(
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await service.get_permissions(current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/policies")
async def create_policy(
    policy: PolicyCreate,
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await service.create_policy(current_user, policy.sub, policy.obj, policy.act)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/policies")
async def delete_policy(
    sub: str,
    obj: str,
    act: str,
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await service.delete_policy(current_user, sub, obj, act)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/roles/assign")
async def assign_role(
    role_data: RoleAssign,
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await service.assign_role(current_user, role_data.user, role_data.role)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/roles/assign")
async def unassign_role(
    user: str,
    role: str,
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await service.unassign_role(current_user, user, role)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/roles/{user}")
async def get_user_role_list(
    user: str,
    service: AdminService = Depends(get_admin_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await service.get_user_roles(current_user, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/policies/reload")
async def reload_policies_endpoint(
    force: bool = True,
    current_user: UserContext = Depends(get_current_active_user),
):
    from app.core.casbin_policy import reload_policies
    
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await reload_policies()
    return result