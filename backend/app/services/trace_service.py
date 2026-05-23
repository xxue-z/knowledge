"""链路追踪服务 - 数据查询和权限控制"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class TraceSession:
    """Trace Session 模型（内存）"""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TraceSpan:
    """Trace Span 模型（内存）"""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TraceEvent:
    """Trace Event 模型（内存）"""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class UserContext:
    """用户上下文"""
    def __init__(self, user_id: str = "", roles: List[str] = None, **kwargs):
        self.user_id = user_id
        self.roles = roles or []


class TracePermission:
    """Trace 权限控制"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def can_view_trace(self, user: UserContext, session: TraceSession) -> bool:
        """判断用户是否可以查看某个 Trace"""
        if "admin" in user.roles:
            return True

        if session.user_id == user.user_id:
            return True

        if "manager" in user.roles:
            return await self._is_subordinate(user.user_id, session.user_id)

        return False

    async def can_view_summary(self, user: UserContext, session: TraceSession) -> bool:
        """判断用户是否可以查看概要（经理可以看下属概要）"""
        if "admin" in user.roles:
            return True

        if session.user_id == user.user_id:
            return True

        if "manager" in user.roles:
            return await self._is_subordinate(user.user_id, session.user_id)

        return False

    async def _is_subordinate(self, manager_id: str, user_id: str) -> bool:
        """判断 user_id 是否是 manager_id 的下属"""
        subordinate_ids = await self._get_subordinates(manager_id)
        return user_id in subordinate_ids

    async def _get_subordinates(self, manager_id: str) -> List[str]:
        """获取指定经理的所有下属 ID（递归）"""
        result = await self.db.execute(
            select(Employee.employee_id).where(Employee.manager_id == manager_id)
        )
        subordinates = list(result.scalars().all())

        all_subordinates = list(subordinates)
        for sub_id in subordinates:
            sub_subordinates = await self._get_subordinates(sub_id)
            all_subordinates.extend(sub_subordinates)

        return all_subordinates

    async def get_viewable_user_ids(self, user: UserContext) -> List[str]:
        """获取用户可查看的 user_id 列表"""
        if "admin" in user.roles:
            return []

        viewable = [user.user_id]

        if "manager" in user.roles:
            subordinates = await self._get_subordinates(user.user_id)
            viewable.extend(subordinates)

        return viewable


class TraceService:
    """链路追踪服务"""

    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user
        self.permission = TracePermission(db)

    async def list_traces(
        self,
        page: int = 1,
        page_size: int = 20,
        start_date: datetime = None,
        end_date: datetime = None,
        status: str = None,
        intent: str = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """获取 Trace 列表"""
        query = ("SELECT * FROM trace_sessions WHERE 1=1")

        viewable_user_ids = await self.permission.get_viewable_user_ids(self.user)

        if viewable_user_ids:
            placeholders = ", ".join([f"'{uid}'" for uid in viewable_user_ids])
            query += f" AND user_id IN ({placeholders})"
        elif user_id:
            temp_session = TraceSession(user_id=user_id)
            if await self.permission.can_view_summary(self.user, temp_session):
                query += f" AND user_id = '{user_id}'"

        if start_date:
            query += f" AND start_time >= '{start_date.isoformat()}'"
        if end_date:
            query += f" AND end_time <= '{end_date.isoformat()}'"
        if status:
            query += f" AND status = '{status}'"
        if intent:
            query += f" AND intent = '{intent}'"

        count_query = f"SELECT COUNT(*) FROM ({query}) AS total"
        total_result = await self.db.execute(text(count_query))
        total = total_result.scalar() or 0

        query += f" ORDER BY start_time DESC LIMIT {page_size} OFFSET {(page - 1) * page_size}"

        result = await self.db.execute(text(query))
        rows = result.fetchall()

        traces = []
        for row in rows:
            session = TraceSession(
                trace_id=row[1] if len(row) > 1 else "",
                request_id=row[2] if len(row) > 2 else "",
                user_id=row[3] if len(row) > 3 else "",
                username=row[4] if len(row) > 4 else "",
                endpoint=row[5] if len(row) > 5 else "",
                method=row[6] if len(row) > 6 else "",
                question=row[7] if len(row) > 7 else "",
                intent=row[8] if len(row) > 8 else "",
                status=row[9] if len(row) > 9 else "",
                total_spans=row[10] if len(row) > 10 else 0,
                success_count=row[12] if len(row) > 12 else 0,
                error_count=row[13] if len(row) > 13 else 0,
                start_time=row[14] if len(row) > 14 else None,
                duration_ms=row[16] if len(row) > 16 else None,
                result_summary=row[17] if len(row) > 17 else ""
            )

            is_owner = session.user_id == self.user.user_id
            can_view = await self.permission.can_view_trace(self.user, session)
            can_view_summary = await self.permission.can_view_summary(self.user, session)

            trace_info = {
                "trace_id": session.trace_id,
                "request_id": session.request_id,
                "user_id": session.user_id,
                "username": session.username,
                "endpoint": session.endpoint,
                "intent": session.intent,
                "status": session.status,
                "start_time": session.start_time.isoformat() if session.start_time else None,
                "duration_ms": session.duration_ms,
                "total_spans": session.total_spans,
                "success_count": session.success_count,
                "error_count": session.error_count,
                "result_summary": session.result_summary if can_view else None,
                "is_owner": is_owner,
                "view_level": "full" if can_view else ("summary" if can_view_summary else "none")
            }
            traces.append(trace_info)

        return {
            "traces": traces,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if total else 0
        }

    async def get_trace_detail(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """获取 Trace 详情（包含 Spans）"""
        query = text("SELECT * FROM trace_sessions WHERE trace_id = :trace_id")
        result = await self.db.execute(query, {"trace_id": trace_id})
        row = result.fetchone()

        if not row:
            return None

        session = TraceSession(
            trace_id=row[1], request_id=row[2], user_id=row[3], username=row[4],
            endpoint=row[5], method=row[6], question=row[7], intent=row[8],
            status=row[9], total_spans=row[10], success_count=row[12],
            error_count=row[13], start_time=row[14], end_time=row[15],
            duration_ms=row[16], result_summary=row[17], output_preview=row[18]
        )

        if not await self.permission.can_view_trace(self.user, session):
            return {"error": "Permission denied", "code": 403}

        is_owner = session.user_id == self.user.user_id

        spans_query = text(
            "SELECT * FROM trace_spans WHERE trace_id = :trace_id ORDER BY start_time"
        )
        spans_result = await self.db.execute(spans_query, {"trace_id": trace_id})
        span_rows = spans_result.fetchall()

        formatted_spans = []
        for span_row in span_rows:
            span = TraceSpan(
                span_id=span_row[2], parent_span_id=span_row[3], agent_id=span_row[5],
                agent_name=span_row[6], action=span_row[7], status=span_row[10],
                error_message=span_row[11], start_time=span_row[12], end_time=span_row[13],
                duration_ms=span_row[14], confidence=span_row[15], sources_count=span_row[16]
            )

            if is_owner:
                events_query = text(
                    "SELECT * FROM trace_events WHERE span_id = :span_id ORDER BY timestamp"
                )
                events_result = await self.db.execute(events_query, {"span_id": span.span_id})
                event_rows = events_result.fetchall()
                events = [
                    {
                        "event_id": e[0],
                        "event_type": e[3],
                        "event_name": e[4],
                        "data": e[5],
                        "timestamp": e[6].isoformat() if e[6] else None
                    }
                    for e in event_rows
                ]
            else:
                events = []

            formatted_span = {
                "span_id": span.span_id,
                "parent_span_id": span.parent_span_id,
                "agent_id": span.agent_id,
                "agent_name": span.agent_name,
                "action": span.action,
                "status": span.status,
                "error_message": span.error_message if is_owner else None,
                "start_time": span.start_time.isoformat() if span.start_time else None,
                "end_time": span.end_time.isoformat() if span.end_time else None,
                "duration_ms": span.duration_ms,
                "confidence": span.confidence,
                "events": events
            }
            formatted_spans.append(formatted_span)

        return {
            "trace_id": session.trace_id,
            "request_id": session.request_id,
            "user_id": session.user_id,
            "username": session.username,
            "endpoint": session.endpoint,
            "method": session.method,
            "question": session.question if is_owner else None,
            "intent": session.intent,
            "status": session.status,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "duration_ms": session.duration_ms,
            "result_summary": session.result_summary if is_owner else None,
            "output_preview": session.output_preview if is_owner else None,
            "total_spans": session.total_spans,
            "success_count": session.success_count,
            "error_count": session.error_count,
            "spans": formatted_spans,
            "view_level": "full" if is_owner else "summary"
        }

    async def get_trace_summary(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """获取 Trace 概要（不包含详情）"""
        query = text("SELECT * FROM trace_sessions WHERE trace_id = :trace_id")
        result = await self.db.execute(query, {"trace_id": trace_id})
        row = result.fetchone()

        if not row:
            return None

        session = TraceSession(
            trace_id=row[1], user_id=row[3], username=row[4], intent=row[8],
            status=row[9], start_time=row[14], duration_ms=row[16],
            total_spans=row[10], success_count=row[12], error_count=row[13]
        )

        if not await self.permission.can_view_summary(self.user, session):
            return {"error": "Permission denied", "code": 403}

        is_owner = session.user_id == self.user.user_id

        return {
            "trace_id": session.trace_id,
            "user_id": session.user_id,
            "username": session.username,
            "intent": session.intent,
            "status": session.status,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "duration_ms": session.duration_ms,
            "total_spans": session.total_spans,
            "success_count": session.success_count,
            "error_count": session.error_count,
            "is_owner": is_owner,
            "view_level": "full" if is_owner else "summary"
        }

    async def get_user_stats(
        self,
        user_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """获取用户统计信息"""
        target_user_id = user_id or self.user.user_id

        temp_session = TraceSession(user_id=target_user_id)
        if not await self.permission.can_view_trace(self.user, temp_session):
            return {"error": "Permission denied", "code": 403}

        query = "SELECT * FROM trace_sessions WHERE user_id = :user_id"
        params = {"user_id": target_user_id}

        if start_date:
            query += " AND start_time >= :start_date"
            params["start_date"] = start_date.isoformat()
        if end_date:
            query += " AND start_time <= :end_date"
            params["end_date"] = end_date.isoformat()

        result = await self.db.execute(text(query), params)
        rows = result.fetchall()

        total_requests = len(rows)
        success_requests = sum(1 for r in rows if r[9] == "completed")
        failed_requests = sum(1 for r in rows if r[9] == "error")

        durations = [r[16] for r in rows if r[16]]
        avg_duration = sum(durations) / len(durations) if durations else 0
        p95_duration = sorted(durations)[int(len(durations) * 0.95)] if durations and len(durations) > 1 else avg_duration

        spans_query = text(
            "SELECT agent_id FROM trace_spans WHERE session_id IN "
            "(SELECT id FROM trace_sessions WHERE user_id = :user_id)"
        )
        spans_result = await self.db.execute(spans_query, {"user_id": target_user_id})
        agent_usage: Dict[str, int] = {}
        for sr in spans_result.fetchall():
            agent_id = sr[0]
            agent_usage[agent_id] = agent_usage.get(agent_id, 0) + 1

        intents_query = text(
            "SELECT intent, COUNT(*) FROM trace_sessions WHERE user_id = :user_id GROUP BY intent"
        )
        intents_result = await self.db.execute(intents_query, {"user_id": target_user_id})
        intent_distribution: Dict[str, int] = {}
        for ir in intents_result.fetchall():
            intent_distribution[ir[0] or "unknown"] = ir[1]

        return {
            "user_id": target_user_id,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "total_requests": total_requests,
            "success_requests": success_requests,
            "failed_requests": failed_requests,
            "success_rate": success_requests / total_requests if total_requests > 0 else 0,
            "avg_duration_ms": avg_duration,
            "p95_duration_ms": p95_duration,
            "agent_usage": agent_usage,
            "intent_distribution": intent_distribution
        }

    async def get_team_stats(
        self,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """获取团队统计信息（经理查看下属汇总）"""
        if "manager" not in self.user.roles and "admin" not in self.user.roles:
            return {"error": "Permission denied", "code": 403}

        subordinates = await self.permission._get_subordinates(self.user.user_id) if "manager" in self.user.roles else []
        user_ids = [self.user.user_id] + subordinates

        if not user_ids:
            return {
                "team_size": 1,
                "total_requests": 0,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "user_stats": []
            }

        placeholders = ", ".join([f"'{uid}'" for uid in user_ids])
        query = f"SELECT * FROM trace_sessions WHERE user_id IN ({placeholders})"

        if start_date:
            query += f" AND start_time >= '{start_date.isoformat()}'"
        if end_date:
            query += f" AND start_time <= '{end_date.isoformat()}'"

        result = await self.db.execute(text(query))
        rows = result.fetchall()

        user_stats: Dict[str, Dict] = {}
        for row in rows:
            uid = row[3]
            if uid not in user_stats:
                user_stats[uid] = {
                    "user_id": uid,
                    "username": row[4],
                    "total_requests": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "total_duration_ms": 0
                }

            user_stats[uid]["total_requests"] += 1
            if row[9] == "completed":
                user_stats[uid]["success_count"] += 1
            elif row[9] == "error":
                user_stats[uid]["error_count"] += 1
            if row[16]:
                user_stats[uid]["total_duration_ms"] += row[16]

        for uid, stats in user_stats.items():
            if stats["total_requests"] > 0:
                stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["total_requests"]
                stats["success_rate"] = stats["success_count"] / stats["total_requests"]

        return {
            "team_size": len(user_stats),
            "total_requests": sum(s["total_requests"] for s in user_stats.values()),
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "user_stats": list(user_stats.values())
        }
