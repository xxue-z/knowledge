from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.dal.postgres import PostgreSQLAdapter
from app.dal.repositories import AuditLogRepository


class AdminService:
    def __init__(self, db_session: AsyncSession = None):
        if db_session:
            self.db_session = db_session
            self.use_session = True
        else:
            self.adapter = PostgreSQLAdapter()
            self.use_session = False
        self.audit_log_repo = AuditLogRepository(self.adapter)
    
    async def query_audit_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """查询审计日志列表"""
        logs = await self.audit_log_repo.query(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
            action=action,
            page=page,
            page_size=page_size
        )
        
        total = await self.audit_log_repo.count(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
            action=action
        )
        
        return {
            "items": [log.to_dict() for log in logs],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def get_audit_log_detail(self, log_id: int):
        """获取审计日志详情"""
        if self.use_session:
            from app.models.audit import AuditLog
            result = await self.db_session.execute(
                __import__('sqlalchemy').select(AuditLog).where(AuditLog.id == log_id)
            )
            log = result.scalar_one_or_none()
        else:
            log = await self.audit_log_repo.get_by_id(log_id)
        
        if log:
            return log.to_dict()
        return None
    
    async def export_audit_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None
    ) -> str:
        """导出审计日志为CSV"""
        logs = await self.audit_log_repo.export(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
            action=action,
            limit=10000
        )
        
        lines = ["user_id,username,action,resource,status,ip_address,created_at,extra"]
        for log in logs:
            log_dict = log.to_dict()
            line = f'"{log_dict.get("user_id", "")}","{log_dict.get("username", "")}","{log_dict.get("action", "")}","{log_dict.get("resource", "")}","{log_dict.get("status", "")}","{log_dict.get("ip_address", "")}","{log_dict.get("created_at", "")}","{log_dict.get("extra", "").replace('"', '""')}"'
            lines.append(line)
        
        return "\n".join(lines)
