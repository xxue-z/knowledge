from fastapi import APIRouter, Depends, Query, HTTPException

from app.core.security import get_current_active_user
from app.models.schemas import UserContext, AuditLogResponse, PolicyCreate, RoleAssign
from app.server import get_admin_server, AdminServer

router = APIRouter()


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    user_id: str | None = None,
    action: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await server.get_audit_logs(current_user, user_id, action, page, page_size)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/users")
async def list_users(
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await server.list_users(current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/permissions")
async def get_permissions(
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await server.get_permissions(current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/policies")
async def create_policy(
    policy: PolicyCreate,
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await server.create_policy(current_user, policy.sub, policy.obj, policy.act)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/policies")
async def delete_policy(
    sub: str,
    obj: str,
    act: str,
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await server.delete_policy(current_user, sub, obj, act)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/roles/assign")
async def assign_role(
    role_data: RoleAssign,
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await server.assign_role(current_user, role_data.user, role_data.role)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/roles/assign")
async def unassign_role(
    user: str,
    role: str,
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        result = await server.unassign_role(current_user, user, role)
        return {"success": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/roles/{user}")
async def get_user_role_list(
    user: str,
    server: AdminServer = Depends(get_admin_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    try:
        return await server.get_user_roles(current_user, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
