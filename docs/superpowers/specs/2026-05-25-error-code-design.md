# 异常码体系设计文档

## 1. 需求分析

### 1.1 需求描述
消除前端和后端代码中的中文字符串比较，统一使用五位数异常码进行错误处理。后端返回异常码，前端根据异常码显示对应的国际化提示信息。

### 1.2 功能要求
- 异常码格式：五位数，前两位表示模块，后三位表示异常编号
- 后端返回统一的异常响应格式（包含 error_code）
- 前端根据 error_code 查找对应的国际化消息
- 创建异常码文档，维护所有异常码的含义

### 1.3 模块编号规划

| 模块编号 | 模块名称 | 说明 |
|----------|----------|------|
| **00** | 系统运行异常 | 运行时错误、数据库连接失败、服务不可用等 |
| 10 | 系统配置模块 | 系统状态、配置管理、初始化等 |
| 11 | 认证模块 | 登录、token、权限等 |
| 12 | Wiki 模块 | Wiki 文档 CRUD |
| 13 | 问答模块 | 智能问答相关 |
| 14 | 知识导航模块 | 导航树管理 |
| 15 | 管理模块 | 管理员操作、审计日志 |
| 16 | 存储模块 | 对象存储操作 |
| 17 | 标签模块 | 标签管理 |
| 18 | 切片规则模块 | 文档切片规则 |
| 99 | 通用模块 | 通用错误（如参数校验失败） |

---

## 2. 响应格式设计

### 2.1 异常响应格式

**成功响应**（保持不变）：
```json
{
  "data": {...}
}
```

**异常响应**：
```json
{
  "error_code": "11001",
  "message": "Built-in admin is disabled",
  "detail": "Please use the admin account you created"
}
```

### 2.2 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| error_code | string | 五位数异常码 |
| message | string | 简短错误描述（英文） |
| detail | string | 详细错误信息（可选） |

---

## 3. 异常码定义

### 3.1 00xxx - 系统运行异常

| 异常码 | 描述 | HTTP 状态码 |
|--------|------|-------------|
| 00001 | 数据库连接失败 | 503 |
| 00002 | Redis 连接失败 | 503 |
| 00003 | Milvus 连接失败 | 503 |
| 00004 | LLM 服务不可用 | 503 |
| 00005 | Keycloak 服务不可用 | 503 |

### 3.2 10xxx - 系统配置模块

| 异常码 | 描述 | HTTP 状态码 |
|--------|------|-------------|
| 10001 | 系统已初始化 | 400 |
| 10002 | 管理员密码长度不足 | 400 |
| 10003 | 配置文件写入失败 | 500 |
| 10004 | 数据库表创建失败 | 500 |

### 3.3 11xxx - 认证模块

| 异常码 | 描述 | HTTP 状态码 |
|--------|------|-------------|
| 11001 | 内置管理员已停用 | 403 |
| 11002 | 用户名或密码错误 | 401 |
| 11003 | Token 过期或无效 | 401 |
| 11004 | 权限不足 | 403 |
| 11005 | Keycloak 认证失败 | 401 |
| 11006 | 旧密码不正确 | 400 |
| 11007 | 新密码长度不足 | 400 |

### 3.4 99xxx - 通用模块

| 异常码 | 描述 | HTTP 状态码 |
|--------|------|-------------|
| 99001 | 参数校验失败 | 400 |
| 99002 | 资源不存在 | 404 |
| 99003 | 请求方法不允许 | 405 |
| 99004 | 请求过期 | 403 |
| 99005 | 签名验证失败 | 403 |
| 99006 | 缺少签名头 | 403 |

---

## 4. 架构设计

### 4.1 后端架构

```
┌─────────────────────────────────────────────────────────────┐
│                     后端异常处理                           │
├─────────────────────────────────────────────────────────────┤
│  ErrorCode 枚举类                                          │
│  - 定义所有异常码                                          │
│  - 包含异常码、HTTP状态码、消息                            │
├─────────────────────────────────────────────────────────────┤
│  CustomException 自定义异常类                              │
│  - 继承 HTTPException                                     │
│  - 自动添加 error_code 字段                                │
├─────────────────────────────────────────────────────────────┤
│  全局异常处理器                                            │
│  - 捕获所有异常                                            │
│  - 统一转换为标准异常响应格式                               │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 前端架构

```
┌─────────────────────────────────────────────────────────────┐
│                     前端异常处理                           │
├─────────────────────────────────────────────────────────────┤
│  errorCodes.js 异常码映射表                                │
│  - key: error_code                                         │
│  - value: i18n key                                        │
├─────────────────────────────────────────────────────────────┤
│  i18n 国际化消息                                           │
│  - zh-CN/errors.js                                        │
│  - en-US/errors.js                                        │
├─────────────────────────────────────────────────────────────┤
│  请求拦截器                                                │
│  - 解析 error_code                                         │
│  - 查找对应的 i18n 消息                                   │
│  - 显示错误提示                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 实现方案

### 5.1 后端实现

**a. 创建异常码枚举类** (`app/core/error_codes.py`)：
```python
from enum import Enum

class ErrorCode(Enum):
    BUILTIN_ADMIN_DISABLED = ("11001", 403, "Built-in admin is disabled")
    INVALID_CREDENTIALS = ("11002", 401, "Invalid username or password")
    # ... 更多异常码
    
    @property
    def code(self):
        return self.value[0]
    
    @property
    def status_code(self):
        return self.value[1]
    
    @property
    def message(self):
        return self.value[2]
```

**b. 创建自定义异常类** (`app/core/exceptions.py`)：
```python
from fastapi import HTTPException

class CustomException(HTTPException):
    def __init__(self, error_code: ErrorCode, detail: str = None):
        super().__init__(
            status_code=error_code.status_code,
            detail={
                "error_code": error_code.code,
                "message": error_code.message,
                "detail": detail or error_code.message
            }
        )
```

**c. 全局异常处理器** (`app/core/exception_handler.py`)：
```python
from fastapi import Request
from fastapi.responses import JSONResponse

async def custom_exception_handler(request: Request, exc: Exception):
    # 统一处理所有异常，返回标准格式
    pass
```

### 5.2 前端实现

**a. 创建异常码映射表** (`src/utils/errorCodes.js`)：
```javascript
export const errorCodes = {
  '11001': 'errors.builtinAdminDisabled',
  '11002': 'errors.invalidCredentials',
  // ... 更多映射
}
```

**b. 修改请求拦截器** (`src/api/request.js`)：
```javascript
// 根据 error_code 查找并显示国际化消息
```

**c. 添加国际化消息** (`src/i18n/zh-CN/errors.js` 和 `en-US/errors.js`)

---

## 6. 迁移步骤

1. 创建异常码定义文件
2. 创建自定义异常类和全局处理器
3. 修改后端所有 HTTPException 使用新的异常码
4. 创建前端异常码映射表
5. 添加国际化消息
6. 修改前端请求拦截器
7. 创建异常码文档

---

## 7. 代码安全性

- 异常码不泄露敏感信息
- 详细错误信息仅在 DEBUG 模式下返回
- 日志记录异常码便于审计
