"""链路追踪模块 - 为每次请求生成唯一追踪 ID"""

import uuid
import logging
from contextvars import ContextVar
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


_trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_start_time: ContextVar[Optional[datetime]] = ContextVar("start_time", default=None)


@dataclass
class TraceContext:
    """追踪上下文"""
    trace_id: str = ""
    request_id: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    parent_span_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "start_time": self.start_time.isoformat() if self.start_time else None
        }


_current_trace_context: ContextVar[Optional[TraceContext]] = ContextVar("trace_context", default=None)


class TraceManager:
    """链路追踪管理器"""
    
    @staticmethod
    def generate_trace_id() -> str:
        """生成链路 ID"""
        return f"tr-{uuid.uuid4().hex[:16]}"
    
    @staticmethod
    def generate_request_id() -> str:
        """生成请求 ID"""
        return f"req-{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def generate_span_id() -> str:
        """生成 span ID"""
        return f"sp-{uuid.uuid4().hex[:8]}"
    
    @classmethod
    def start_trace(cls, endpoint: str = None, method: str = None, user_id: str = None) -> TraceContext:
        """开始追踪"""
        trace_id = cls.generate_trace_id()
        request_id = cls.generate_request_id()
        span_id = cls.generate_span_id()
        start_time = datetime.now()
        
        context = TraceContext(
            trace_id=trace_id,
            request_id=request_id,
            start_time=start_time,
            span_id=span_id,
            user_id=user_id,
            endpoint=endpoint,
            method=method
        )
        
        _trace_id.set(trace_id)
        _request_id.set(request_id)
        _start_time.set(start_time)
        _current_trace_context.set(context)
        
        logger.info(f"[{trace_id}] Trace started: {method} {endpoint}")
        
        return context
    
    @classmethod
    def get_trace_id(cls) -> Optional[str]:
        """获取当前链路 ID"""
        return _trace_id.get()
    
    @classmethod
    def get_request_id(cls) -> Optional[str]:
        """获取当前请求 ID"""
        return _request_id.get()
    
    @classmethod
    def get_current_context(cls) -> Optional[TraceContext]:
        """获取当前追踪上下文"""
        return _current_trace_context.get()
    
    @classmethod
    def end_trace(cls):
        """结束追踪"""
        trace_id = _trace_id.get()
        start_time = _start_time.get()
        
        if trace_id and start_time:
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{trace_id}] Trace ended, duration: {duration:.3f}s")
        
        _trace_id.set(None)
        _request_id.set(None)
        _start_time.set(None)
        _current_trace_context.set(None)
    
    @classmethod
    def create_span(cls, name: str, parent_span_id: str = None) -> str:
        """创建新的 span"""
        span_id = cls.generate_span_id()
        trace_id = cls.get_trace_id()
        
        logger.debug(f"[{trace_id}] Span created: {name} [{span_id}]")
        
        return span_id


class LogFormatter(logging.Formatter):
    """自定义日志格式，包含追踪 ID"""
    
    def format(self, record: logging.LogRecord) -> str:
        trace_id = _trace_id.get() or "-"
        request_id = _request_id.get() or "-"
        
        record.trace_id = trace_id
        record.request_id = request_id
        
        return super().format(record)


def setup_trace_logging(log_dir: str = "logs", level: str = "INFO"):
    """设置带追踪的日志配置"""
    import os
    from app.core.logging import ensure_log_dir
    
    ensure_log_dir(log_dir)
    
    trace_handler = logging.StreamHandler()
    trace_handler.setLevel(getattr(logging, level.upper()))
    trace_handler.setFormatter(LogFormatter(
        fmt="%(asctime)s | %(levelname)-8s | [%(trace_id)s] [%(request_id)s] | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    
    trace_file_handler = logging.FileHandler(
        os.path.join(log_dir, "trace.log"),
        encoding="utf-8"
    )
    trace_file_handler.setLevel(getattr(logging, level.upper()))
    trace_file_handler.setFormatter(LogFormatter(
        fmt="%(asctime)s | %(levelname)-8s | [%(trace_id)s] [%(request_id)s] | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    
    root_logger = logging.getLogger()
    root_logger.addHandler(trace_handler)
    root_logger.addHandler(trace_file_handler)
    
    return trace_handler, trace_file_handler
