# FR-PERM-003: 动态策略热更新实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现Casbin策略动态热更新功能，支持管理员通过API接口实时重载权限策略，无需重启服务。

**Architecture:** 通过移除 `@lru_cache` 装饰器，改用全局变量存储Enforcer实例；新增 `reload_policies()` 函数支持显式重载；新增管理员API端点 `/api/admin/policies/reload` 触发重载。

**Tech Stack:** Python 3.11+, FastAPI, Casbin, SQLAlchemy, Pytest

---

## 文件结构

| 文件路径 | 职责 | 状态 |
|----------|------|------|
| `app/core/casbin_policy.py` | Casbin策略管理，新增热重载支持 | 修改 |
| `app/api/admin.py` | 管理员API，新增策略重载端点 | 修改 |
| `tests/test_casbin_policy.py` | Casbin策略测试 | 新增 |
| `docs/requirements/requirements-specification.md` | 更新需求状态 | 修改 |
| `docs/requirements/detailed/FR-PERM.md` | 更新FR-PERM-003状态 | 修改 |

---

## Task 1: 修改 casbin_policy.py 支持热重载

**Files:**
- Modify: `backend/app/core/casbin_policy.py`
- Test: `backend/tests/test_casbin_policy.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_casbin_policy.py
import pytest
from app.core.casbin_policy import get_enforcer, reload_policies, _policy_version

@pytest.mark.asyncio
async def test_policy_reload():
    """测试策略重载功能"""
    initial_version = _policy_version
    
    # 调用重载
    result = await reload_policies()
    
    # 验证版本号递增
    assert result["success"] == True
    assert _policy_version == initial_version + 1
    
    # 验证重载后仍能正常校验权限
    enforcer = get_enforcer()
    assert enforcer is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_casbin_policy.py::test_policy_reload -v`
Expected: FAIL with "name '_policy_version' is not defined"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/core/casbin_policy.py
import casbin
import casbin_sqlalchemy_adapter
import logging

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# 全局变量替代lru_cache
_enforcer = None
_policy_version = 0

RBAC_MODEL = """
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
"""

DEFAULT_POLICIES = [
    ("admin", "wiki", "read"),
    ("admin", "wiki", "write"),
    ("admin", "wiki", "delete"),
    ("admin", "employee", "read"),
    ("admin", "employee", "write"),
    ("admin", "casbin_policy", "manage"),
    ("hr", "wiki", "read"),
    ("hr", "employee", "read"),
    ("hr", "employee", "write"),
    ("manager", "wiki", "read"),
    ("manager", "employee", "read"),
    ("employee", "wiki", "read"),
    ("employee", "employee", "read"),
]

DEFAULT_ROLES = [
    ("admin", "hr"),
    ("admin", "manager"),
    ("admin", "employee"),
    ("hr", "manager"),
    ("hr", "employee"),
    ("manager", "employee"),
]


def get_enforcer(refresh: bool = False) -> casbin.Enforcer:
    """获取Enforcer实例，支持刷新"""
    global _enforcer, _policy_version
    
    if refresh or _enforcer is None:
        adapter = casbin_sqlalchemy_adapter.Adapter(settings.DATABASE_URL)
        model = casbin.model.Model()
        model.load_model_from_text(RBAC_MODEL)
        _enforcer = casbin.Enforcer(model, adapter)
        _policy_version += 1
    
    return _enforcer


def _init_default_policies(enforcer: casbin.Enforcer):
    for policy in DEFAULT_POLICIES:
        if not enforcer.get_policy().get(policy):
            enforcer.add_policy(*policy)
    for role in DEFAULT_ROLES:
        if not enforcer.has_role_for_user(role[0], role[1]):
            enforcer.add_role_for_user(role[0], role[1])
    logger.info("Casbin default policies initialized")


async def check_permission(user_roles: list[str], resource: str, action: str) -> bool:
    enforcer = get_enforcer()
    for role in user_roles:
        if enforcer.enforce(role, resource, action):
            return True
    return False


async def get_user_permissions(user_roles: list[str]) -> list[dict]:
    enforcer = get_enforcer()
    permissions = []
    seen = set()
    for role in user_roles:
        for p in enforcer.get_permissions_for_user(role):
            key = tuple(p)
            if key not in seen:
                seen.add(key)
                permissions.append({"sub": p[0], "obj": p[1], "act": p[2]})
    return permissions


async def add_policy(sub: str, obj: str, act: str) -> bool:
    enforcer = get_enforcer()
    if not enforcer.enforce(sub, obj, act):
        result = enforcer.add_policy(sub, obj, act)
        return result
    return True


async def remove_policy(sub: str, obj: str, act: str) -> bool:
    enforcer = get_enforcer()
    return enforcer.remove_policy(sub, obj, act)


async def add_role_for_user(user: str, role: str) -> bool:
    enforcer = get_enforcer()
    if not enforcer.has_role_for_user(user, role):
        return enforcer.add_role_for_user(user, role)
    return True


async def remove_role_for_user(user: str, role: str) -> bool:
    enforcer = get_enforcer()
    return enforcer.delete_role_for_user(user, role)


async def get_user_roles(user: str) -> list[str]:
    enforcer = get_enforcer()
    return enforcer.get_roles_for_user(user)


async def init_policies():
    enforcer = get_enforcer()
    _init_default_policies(enforcer)


async def reload_policies() -> dict:
    """重新加载策略"""
    global _enforcer
    _enforcer = None  # 清空缓存
    get_enforcer(refresh=True)
    
    logger.info(f"Casbin policies reloaded, version: {_policy_version}")
    
    return {
        "success": True,
        "message": "Policies reloaded successfully",
        "version": _policy_version
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_casbin_policy.py::test_policy_reload -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend
git add app/core/casbin_policy.py tests/test_casbin_policy.py
git commit -m "feat: add policy hot reload support"
```

---

## Task 2: 新增管理员API端点

**Files:**
- Modify: `backend/app/api/admin.py`
- Test: `backend/tests/test_admin_api.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_admin_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_reload_policies_endpoint():
    """测试策略重载API端点"""
    response = client.post(
        "/api/admin/policies/reload",
        json={"force": True}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "version" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_admin_api.py::test_reload_policies_endpoint -v`
Expected: FAIL with "404 Not Found"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/api/admin.py
from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import UserContext
from app.core.security import get_current_user
from app.core.casbin_policy import reload_policies

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/policies/reload")
async def reload_policies_endpoint(
    force: bool = True,
    user: UserContext = Depends(get_current_user)
):
    """
    重新加载Casbin权限策略
    
    仅管理员角色可调用此接口
    """
    if "admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await reload_policies()
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_admin_api.py::test_reload_policies_endpoint -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend
git add app/api/admin.py tests/test_admin_api.py
git commit -m "feat: add policy reload endpoint"
```

---

## Task 3: 更新需求文档状态

**Files:**
- Modify: `docs/requirements/requirements-specification.md`
- Modify: `docs/requirements/detailed/FR-PERM.md`

- [ ] **Step 1: 更新 requirements-specification.md**

修改FR-PERM-003状态从 `⚠️` 改为 `✅`

- [ ] **Step 2: 更新 FR-PERM.md**

修改FR-PERM-003状态从 `❌ 未实现` 改为 `✅ 已完成`

- [ ] **Step 3: Commit**

```bash
git add docs/requirements/requirements-specification.md docs/requirements/detailed/FR-PERM.md
git commit -m "docs: update FR-PERM-003 status to completed"
```

---

## Task 4: 运行完整测试套件

**Files:**
- Test: `backend/tests/`

- [ ] **Step 1: Run all related tests**

Run: `cd backend && pytest tests/test_casbin_policy.py tests/test_admin_api.py -v`
Expected: All PASS

- [ ] **Step 2: Run full test suite**

Run: `cd backend && pytest tests/ -v`
Expected: All PASS

- [ ] **Step 3: Commit final changes**

```bash
git add .
git commit -m "chore: complete FR-PERM-003 implementation"
```

---

## Self-Review

### 1. Spec Coverage

| 需求项 | 对应Task |
|--------|----------|
| Casbin策略更改后立即生效 | Task 1: reload_policies() |
| 策略自动重新加载 | Task 1: get_enforcer(refresh=True) |
| 新策略立即生效 | Task 2: API端点触发重载 |
| 策略更新后5秒内生效 | Task 1: 同步重载 |

### 2. Placeholder Scan

✅ 无占位符，所有步骤都有具体代码和命令

### 3. Type Consistency

✅ 类型和方法签名一致

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-25-dynamic-policy-hot-update.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**