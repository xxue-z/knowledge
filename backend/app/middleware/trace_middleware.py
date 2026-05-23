"""追踪中间件 - 为每个请求注入链路追踪 ID"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.trace import TraceManager

logger = logging.getLogger(__name__)


class TraceMiddleware(BaseHTTPMiddleware):
    """追踪中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_context = None
        
        try:
            trace_context = TraceManager.start_trace(
                endpoint=str(request.url.path),
                method=request.method,
                user_id=self._get_user_id(request)
            )
            
            request.state.trace_context = trace_context
            request.state.trace_id = trace_context.trace_id
            request.state.request_id = trace_context.request_id
            
            logger.info(
                f"Request started: {request.method} {request.url.path}",
                extra={
                    "trace_id": trace_context.trace_id,
                    "request_id": trace_context.request_id
                }
            )
            
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            response.headers["X-Trace-ID"] = trace_context.trace_id
            response.headers["X-Request-ID"] = trace_context.request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)",
                extra={
                    "trace_id": trace_context.trace_id,
                    "request_id": trace_context.request_id,
                    "status_code": response.status_code,
                    "process_time": process_time
                }
            )
            
            return response
            
        except Exception as e:
            if trace_context:
                logger.error(
                    f"Request failed: {request.method} {request.url.path} - {str(e)}",
                    extra={
                        "trace_id": trace_context.trace_id,
                        "request_id": trace_context.request_id
                    },
                    exc_info=True
                )
            raise
            
        finally:
            if trace_context:
                TraceManager.end_trace()
    
    def _get_user_id(self, request: Request) -> str:
        """从请求中获取用户 ID"""
        if hasattr(request.state, "user_id"):
            return request.state.user_id
        
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from app.core.security import decode_token
                token = auth_header[7:]
                payload = decode_token(token)
                return payload.get("sub", "anonymous")
            except:
                pass
        
        return "anonymous"
