from fastapi import HTTPException
from .error_codes import ErrorCode


class CustomException(HTTPException):
    """
    自定义异常类
    统一异常响应格式，包含 error_code 字段
    """
    
    def __init__(self, error_code: ErrorCode, detail: str = None):
        super().__init__(
            status_code=error_code.status_code,
            detail={
                "error_code": error_code.code,
                "message": error_code.message,
                "detail": detail or error_code.message
            }
        )
        self.error_code = error_code
