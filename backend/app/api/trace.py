"""链路追踪 API"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schemas import UserContext
from app.services.trace_service import TraceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trace", tags=["trace"])


class TraceListResponse(BaseModel):
    traces: list
    total: int
    page: int
    page_size: int
    pages: int


class TraceDetailResponse(BaseModel):
    trace_id: str
    request_id: str
    user_id: str
    username: str
    endpoint: str
    method: str
    question: str
    intent: str
    status: str
    start_time: Optional[str]
    end_time: Optional[str]
    duration_ms: float
    result_summary: Optional[str]
    output_preview: Optional[str]
    total_spans: int
    success_count: int
    error_count: int
    spans: list
    error: Optional[str] = None
    code: Optional[int] = None


class TraceSummaryResponse(BaseModel):
    trace_id: str
    user_id: str
    username: str
    intent: str
    status: str
    start_time: Optional[str]
    duration_ms: float
    total_spans: int
    success_count: int
    error_count: int
    is_owner: bool
    view_level: str


class UserStatsResponse(BaseModel):
    user_id: str
    period: dict
    total_requests: int
    success_requests: int
    failed_requests: int
    success_rate: float
    avg_duration_ms: float
    p95_duration_ms: float
    agent_usage: dict
    intent_distribution: dict


class TeamStatsResponse(BaseModel):
    team_size: int
    total_requests: int
    start_date: Optional[str]
    end_date: Optional[str]
    user_stats: list


@router.get("/list", response_model=TraceListResponse)
async def list_traces(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = None,
    intent: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: UserContext = Depends(get_current_user)
):
    """获取 Trace 列表"""
    db = await get_db()
    try:
        service = TraceService(db, current_user)
        result = await service.list_traces(
            page=page,
            page_size=page_size,
            start_date=start_date,
            end_date=end_date,
            status=status,
            intent=intent,
            user_id=user_id
        )
        return result
    finally:
        await db.close()


@router.get("/{trace_id}", response_model=TraceDetailResponse)
async def get_trace_detail(
    trace_id: str,
    current_user: UserContext = Depends(get_current_user)
):
    """获取 Trace 详情"""
    db = await get_db()
    try:
        service = TraceService(db, current_user)
        result = await service.get_trace_detail(trace_id)
        
        if result is None:
            return TraceDetailResponse(
                trace_id=trace_id,
                request_id="",
                user_id="",
                username="",
                endpoint="",
                method="",
                question="",
                intent="",
                status="",
                duration_ms=0,
                total_spans=0,
                success_count=0,
                error_count=0,
                spans=[],
                error="Trace not found",
                code=404
            )
        
        if result.get("error"):
            return TraceDetailResponse(
                trace_id=trace_id,
                request_id="",
                user_id="",
                username="",
                endpoint="",
                method="",
                question="",
                intent="",
                status="",
                duration_ms=0,
                total_spans=0,
                success_count=0,
                error_count=0,
                spans=[],
                error=result["error"],
                code=result.get("code", 403)
            )
        
        return result
    finally:
        await db.close()


@router.get("/{trace_id}/summary", response_model=TraceSummaryResponse)
async def get_trace_summary(
    trace_id: str,
    current_user: UserContext = Depends(get_current_user)
):
    """获取 Trace 概要"""
    db = await get_db()
    try:
        service = TraceService(db, current_user)
        result = await service.get_trace_summary(trace_id)
        
        if result is None:
            return TraceSummaryResponse(
                trace_id=trace_id,
                user_id="",
                username="",
                intent="",
                status="",
                duration_ms=0,
                total_spans=0,
                success_count=0,
                error_count=0,
                is_owner=False,
                view_level="none"
            )
        
        if result.get("error"):
            return TraceSummaryResponse(
                trace_id=trace_id,
                user_id="",
                username="",
                intent="",
                status="",
                duration_ms=0,
                total_spans=0,
                success_count=0,
                error_count=0,
                is_owner=False,
                view_level="none"
            )
        
        return result
    finally:
        await db.close()


@router.get("/stats/user", response_model=UserStatsResponse)
async def get_user_stats(
    request: Request,
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: UserContext = Depends(get_current_user)
):
    """获取用户统计"""
    db = await get_db()
    try:
        service = TraceService(db, current_user)
        result = await service.get_user_stats(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if result.get("error"):
            return UserStatsResponse(
                user_id=user_id or current_user.user_id,
                period={},
                total_requests=0,
                success_requests=0,
                failed_requests=0,
                success_rate=0,
                avg_duration_ms=0,
                p95_duration_ms=0,
                agent_usage={},
                intent_distribution={}
            )
        
        return result
    finally:
        await db.close()


@router.get("/stats/team", response_model=TeamStatsResponse)
async def get_team_stats(
    request: Request,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: UserContext = Depends(get_current_user)
):
    """获取团队统计"""
    db = await get_db()
    try:
        service = TraceService(db, current_user)
        result = await service.get_team_stats(
            start_date=start_date,
            end_date=end_date
        )
        
        if result.get("error"):
            return TeamStatsResponse(
                team_size=0,
                total_requests=0,
                start_date=None,
                end_date=None,
                user_stats=[]
            )
        
        return result
    finally:
        await db.close()
