import casbin
import casbin_sqlalchemy_adapter
import logging
from functools import lru_cache

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

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


@lru_cache()
def get_enforcer() -> casbin.Enforcer:
    adapter = casbin_sqlalchemy_adapter.Adapter(settings.DATABASE_URL)
    model = casbin.model.Model()
    model.load_model_from_text(RBAC_MODEL)
    enforcer = casbin.Enforcer(model, adapter)
    return enforcer


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
