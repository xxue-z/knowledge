from enum import Enum


class ErrorCode(Enum):
    """
    异常码枚举类
    
    异常码格式：五位数
    - 前两位：模块编号
    - 后三位：异常编号
    
    模块编号：
    - 00：系统运行异常
    - 10：系统配置模块
    - 11：认证模块
    - 12：Wiki 模块
    - 13：问答模块
    - 14：知识导航模块
    - 15：管理模块
    - 16：存储模块
    - 17：标签模块
    - 18：切片规则模块
    - 99：通用模块
    """
    
    # 00xxx - 系统运行异常
    DB_CONNECTION_FAILED = ("00001", 503, "Database connection failed")
    REDIS_CONNECTION_FAILED = ("00002", 503, "Redis connection failed")
    MILVUS_CONNECTION_FAILED = ("00003", 503, "Milvus connection failed")
    LLM_SERVICE_UNAVAILABLE = ("00004", 503, "LLM service unavailable")
    KEYCLOAK_UNAVAILABLE = ("00005", 503, "Keycloak service unavailable")
    
    # 10xxx - 系统配置模块
    SYSTEM_ALREADY_INITIALIZED = ("10001", 400, "System is already initialized")
    ADMIN_PASSWORD_TOO_SHORT = ("10002", 400, "Admin password too short")
    CONFIG_FILE_WRITE_FAILED = ("10003", 500, "Config file write failed")
    DB_TABLE_CREATE_FAILED = ("10004", 500, "Database table creation failed")
    
    # 11xxx - 认证模块
    BUILTIN_ADMIN_DISABLED = ("11001", 403, "Built-in admin is disabled")
    INVALID_CREDENTIALS = ("11002", 401, "Invalid username or password")
    TOKEN_EXPIRED = ("11003", 401, "Token expired or invalid")
    INSUFFICIENT_PERMISSIONS = ("11004", 403, "Insufficient permissions")
    KEYCLOAK_AUTH_FAILED = ("11005", 401, "Keycloak authentication failed")
    OLD_PASSWORD_INCORRECT = ("11006", 400, "Old password incorrect")
    NEW_PASSWORD_TOO_SHORT = ("11007", 400, "New password too short")
    
    # 99xxx - 通用模块
    VALIDATION_ERROR = ("99001", 400, "Validation error")
    RESOURCE_NOT_FOUND = ("99002", 404, "Resource not found")
    METHOD_NOT_ALLOWED = ("99003", 405, "Method not allowed")
    REQUEST_EXPIRED = ("99004", 403, "Request expired")
    SIGNATURE_VERIFICATION_FAILED = ("99005", 403, "Signature verification failed")
    MISSING_SIGNATURE_HEADERS = ("99006", 403, "Missing signature headers")
    
    @property
    def code(self) -> str:
        return self.value[0]
    
    @property
    def status_code(self) -> int:
        return self.value[1]
    
    @property
    def message(self) -> str:
        return self.value[2]
