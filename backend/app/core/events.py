"""异步事件发布机制 - 用于链路追踪"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型"""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SPAN_START = "span_start"
    SPAN_END = "span_end"
    EVENT_LOG = "event_log"
    ERROR = "error"
    METRIC = "metric"


@dataclass
class TraceEvent:
    """追踪事件"""
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    event_type: EventType = EventType.EVENT_LOG
    trace_id: str = ""
    span_id: str = ""
    agent_id: str = ""
    agent_name: str = ""
    action: str = ""
    event_name: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: Optional[float] = None


class EventPublisher:
    """事件发布器"""

    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

    def subscribe(self, event_type: EventType, handler: Callable):
        """订阅事件"""
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler for {event_type}")

    def unsubscribe(self, event_type: EventType, handler: Callable):
        """取消订阅"""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    async def publish(self, event: TraceEvent):
        """发布事件到队列"""
        await self._queue.put(event)

    def publish_sync(self, event: TraceEvent):
        """同步发布事件（用于非异步环境）"""
        asyncio.create_task(self._queue.put(event))

    async def start(self):
        """启动事件处理器"""
        if self._running:
            return
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("EventPublisher started")

    async def stop(self):
        """停止事件处理器"""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("EventPublisher stopped")

    async def _process_events(self):
        """处理事件队列"""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)

    async def _dispatch_event(self, event: TraceEvent):
        """分发事件到订阅者"""
        handlers = self._subscribers.get(event.event_type, [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error dispatching event to handler: {e}", exc_info=True)

        if not handlers:
            logger.debug(f"No handlers for event type: {event.event_type}")


class TraceCollector:
    """追踪数据收集器 - 订阅事件并直接写入数据库"""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self._pending_sessions: Dict[str, Dict] = {}
        self._pending_spans: Dict[str, Dict] = {}
        self._pending_events: Dict[str, List[Dict]] = defaultdict(list)
        self._session_span_counts: Dict[str, int] = defaultdict(int)
        self._session_success_counts: Dict[str, int] = defaultdict(int)
        self._session_error_counts: Dict[str, int] = defaultdict(int)
        self._batch_size = 10
        self._flush_interval = 5.0
        self._last_flush = datetime.now()

    async def handle_session_start(self, event: TraceEvent):
        """处理会话开始事件"""
        session = {
            "id": uuid.uuid4().hex,
            "trace_id": event.trace_id,
            "request_id": event.data.get("request_id", ""),
            "user_id": event.data.get("user_id", ""),
            "username": event.data.get("username", ""),
            "endpoint": event.data.get("endpoint", ""),
            "method": event.data.get("method", ""),
            "question": event.data.get("question", ""),
            "intent": event.data.get("intent", ""),
            "status": "running",
            "total_spans": 0,
            "total_events": 0,
            "success_count": 0,
            "error_count": 0,
            "start_time": event.timestamp,
            "end_time": None,
            "duration_ms": None,
            "result_summary": None,
            "output_preview": None
        }

        self._pending_sessions[event.trace_id] = session

    async def handle_session_end(self, event: TraceEvent):
        """处理会话结束事件"""
        session = self._pending_sessions.get(event.trace_id)
        if session:
            session["status"] = event.data.get("status", "completed")
            session["end_time"] = event.timestamp
            session["duration_ms"] = event.duration_ms
            session["result_summary"] = event.data.get("result_summary", "")
            session["output_preview"] = (event.data.get("output_preview", "") or "")[:500]
            session["success_count"] = self._session_success_counts.get(event.trace_id, 0)
            session["error_count"] = self._session_error_counts.get(event.trace_id, 0)
            session["total_spans"] = self._session_span_counts.get(event.trace_id, 0)

            await self._flush_if_needed()

    async def handle_span_start(self, event: TraceEvent):
        """处理 Span 开始事件"""
        session = self._pending_sessions.get(event.trace_id)
        session_id = session["id"] if session else None

        span = {
            "id": uuid.uuid4().hex,
            "trace_id": event.trace_id,
            "span_id": event.span_id,
            "parent_span_id": event.data.get("parent_span_id"),
            "session_id": session_id,
            "agent_id": event.agent_id,
            "agent_name": event.agent_name,
            "action": event.action,
            "input_summary": json.dumps(event.data.get("input_summary")) if event.data.get("input_summary") else None,
            "output_summary": None,
            "status": "running",
            "error_message": None,
            "start_time": event.timestamp,
            "end_time": None,
            "duration_ms": None,
            "confidence": None,
            "sources_count": 0
        }

        self._pending_spans[event.span_id] = span

    async def handle_span_end(self, event: TraceEvent):
        """处理 Span 结束事件"""
        span = self._pending_spans.get(event.span_id)
        if span:
            span["status"] = event.data.get("status", "completed")
            span["end_time"] = event.timestamp
            span["duration_ms"] = event.duration_ms
            output_summary = event.data.get("output_summary")
            if output_summary:
                span["output_summary"] = json.dumps(output_summary) if isinstance(output_summary, dict) else output_summary
            span["confidence"] = event.data.get("confidence")
            span["error_message"] = event.data.get("error_message")
            span["sources_count"] = event.data.get("sources_count", 0)

            self._session_span_counts[event.trace_id] = self._session_span_counts.get(event.trace_id, 0) + 1

            if span["status"] == "error":
                self._session_error_counts[event.trace_id] = self._session_error_counts.get(event.trace_id, 0) + 1
            else:
                self._session_success_counts[event.trace_id] = self._session_success_counts.get(event.trace_id, 0) + 1

    async def handle_event_log(self, event: TraceEvent):
        """处理普通日志事件"""
        trace_event = {
            "id": event.event_id,
            "trace_id": event.trace_id,
            "span_id": event.span_id,
            "event_type": event.event_type.value,
            "event_name": event.event_name or event.message,
            "data": json.dumps(event.data) if event.data else None,
            "message": event.message,
            "timestamp": event.timestamp
        }

        self._pending_events[event.span_id].append(trace_event)

    async def _flush_if_needed(self):
        """必要时刷新到数据库"""
        now = datetime.now()
        elapsed = (now - self._last_flush).total_seconds()

        if len(self._pending_sessions) >= self._batch_size or elapsed >= self._flush_interval:
            await self._flush()

    async def _flush(self):
        """刷新数据到数据库"""
        try:
            async with self.db_session_factory() as db:
                for session in self._pending_sessions.values():
                    await db.execute(
                        text("""
                            INSERT INTO trace_sessions
                            (id, trace_id, request_id, user_id, username, endpoint, method, question, intent,
                             status, total_spans, total_events, success_count, error_count, start_time, end_time,
                             duration_ms, result_summary, output_preview)
                            VALUES
                            (:id, :trace_id, :request_id, :user_id, :username, :endpoint, :method, :question, :intent,
                             :status, :total_spans, :total_events, :success_count, :error_count, :start_time, :end_time,
                             :duration_ms, :result_summary, :output_preview)
                        """),
                        session
                    )

                for span in self._pending_spans.values():
                    await db.execute(
                        text("""
                            INSERT INTO trace_spans
                            (id, trace_id, span_id, parent_span_id, session_id, agent_id, agent_name, action,
                             input_summary, output_summary, status, error_message, start_time, end_time,
                             duration_ms, confidence, sources_count)
                            VALUES
                            (:id, :trace_id, :span_id, :parent_span_id, :session_id, :agent_id, :agent_name, :action,
                             :input_summary, :output_summary, :status, :error_message, :start_time, :end_time,
                             :duration_ms, :confidence, :sources_count)
                        """),
                        span
                    )

                for span_id, events in self._pending_events.items():
                    for event in events:
                        await db.execute(
                            text("""
                                INSERT INTO trace_events
                                (id, trace_id, span_id, event_type, event_name, data, message, timestamp)
                                VALUES
                                (:id, :trace_id, :span_id, :event_type, :event_name, :data, :message, :timestamp)
                            """),
                            event
                        )

                await db.commit()

                self._pending_sessions.clear()
                self._pending_spans.clear()
                self._pending_events.clear()
                self._session_span_counts.clear()
                self._session_success_counts.clear()
                self._session_error_counts.clear()
                self._last_flush = datetime.now()

                logger.debug("Flushed trace data to database")
        except Exception as e:
            logger.error(f"Error flushing trace data: {e}", exc_info=True)

    async def shutdown(self):
        """关闭时刷新所有数据"""
        await self._flush()


from sqlalchemy import text

_global_publisher = EventPublisher()


def get_publisher() -> EventPublisher:
    """获取全局事件发布器"""
    return _global_publisher


async def emit_session_start(
    trace_id: str,
    request_id: str,
    user_id: str,
    username: str,
    endpoint: str = "",
    method: str = "",
    question: str = "",
    intent: str = ""
):
    """发射会话开始事件"""
    event = TraceEvent(
        event_type=EventType.SESSION_START,
        trace_id=trace_id,
        data={
            "request_id": request_id,
            "user_id": user_id,
            "username": username,
            "endpoint": endpoint,
            "method": method,
            "question": question,
            "intent": intent
        }
    )
    await _global_publisher.publish(event)


async def emit_session_end(
    trace_id: str,
    status: str = "completed",
    duration_ms: float = 0,
    result_summary: str = "",
    output_preview: str = "",
    success_count: int = 0,
    error_count: int = 0
):
    """发射会话结束事件"""
    event = TraceEvent(
        event_type=EventType.SESSION_END,
        trace_id=trace_id,
        duration_ms=duration_ms,
        data={
            "status": status,
            "result_summary": result_summary,
            "output_preview": output_preview,
            "success_count": success_count,
            "error_count": error_count
        }
    )
    await _global_publisher.publish(event)


async def emit_span_start(
    trace_id: str,
    span_id: str,
    agent_id: str,
    agent_name: str,
    action: str,
    parent_span_id: str = None,
    input_summary: dict = None
):
    """发射 Span 开始事件"""
    event = TraceEvent(
        event_type=EventType.SPAN_START,
        trace_id=trace_id,
        span_id=span_id,
        agent_id=agent_id,
        agent_name=agent_name,
        action=action,
        data={
            "parent_span_id": parent_span_id,
            "input_summary": input_summary
        }
    )
    await _global_publisher.publish(event)


async def emit_span_end(
    trace_id: str,
    span_id: str,
    agent_id: str,
    status: str = "completed",
    duration_ms: float = 0,
    output_summary: dict = None,
    confidence: float = 0,
    error_message: str = None,
    sources_count: int = 0
):
    """发射 Span 结束事件"""
    event = TraceEvent(
        event_type=EventType.SPAN_END,
        trace_id=trace_id,
        span_id=span_id,
        agent_id=agent_id,
        duration_ms=duration_ms,
        data={
            "status": status,
            "output_summary": output_summary,
            "confidence": confidence,
            "error_message": error_message,
            "sources_count": sources_count
        }
    )
    await _global_publisher.publish(event)


async def emit_event(
    trace_id: str,
    span_id: str,
    agent_id: str,
    event_name: str,
    data: dict = None,
    message: str = ""
):
    """发射普通事件"""
    event = TraceEvent(
        event_type=EventType.EVENT_LOG,
        trace_id=trace_id,
        span_id=span_id,
        agent_id=agent_id,
        event_name=event_name,
        data=data or {},
        message=message
    )
    await _global_publisher.publish(event)


async def start_publisher():
    """启动事件发布器"""
    await _global_publisher.start()


async def stop_publisher():
    """停止事件发布器"""
    await _global_publisher.stop()
