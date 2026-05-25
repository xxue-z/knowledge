from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
import logging

from .error_codes import ErrorCode

logger = logging.getLogger(__name__)


async def custom_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    统一处理所有异常，返回标准异常响应格式
    """
    
    if isinstance(exc, StarletteHTTPException):
        if isinstance(exc.detail, dict) and "error_code" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": str(exc.status_code).zfill(5),
                "message": exc.detail if isinstance(exc.detail, str) else "Unknown error",
                "detail": exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            }
        )
    
    elif isinstance(exc, ValidationError):
        return JSONResponse(
            status_code=400,
            content={
                "error_code": ErrorCode.VALIDATION_ERROR.code,
                "message": ErrorCode.VALIDATION_ERROR.message,
                "detail": exc.errors()
            }
        )
    
    else:
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "00000",
                "message": "Internal server error",
                "detail": str(exc)
            }
        )
