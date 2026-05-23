import uuid
from app.dal.repositories import ChunkingRuleRepository
from app.models.wiki_storage import ChunkingRule


class ChunkingService:
    """切片规则管理服务"""

    def __init__(self, rule_repo: ChunkingRuleRepository):
        self.rule_repo = rule_repo

    async def list_rules(self) -> list[dict]:
        rules = await self.rule_repo.get_all()
        return [self._rule_to_dict(r) for r in rules]

    async def get_active_rules(self) -> list[dict]:
        rules = await self.rule_repo.get_active_rules()
        return [self._rule_to_dict(r) for r in rules]

    async def create_rule(self, name: str, description: str, rule_type: str, rule_config: dict, sort_order: int, created_by: str) -> ChunkingRule:
        rule = ChunkingRule(
            name=name,
            description=description,
            rule_type=rule_type,
            rule_config=rule_config,
            sort_order=sort_order,
        )
        return await self.rule_repo.create(rule)

    async def update_rule(self, rule_id: uuid.UUID, name: str, description: str, rule_type: str, rule_config: dict, is_active: bool) -> ChunkingRule | None:
        rule = await self.rule_repo.get_by_id(rule_id)
        if not rule:
            return None

        rule.name = name
        rule.description = description
        rule.rule_type = rule_type
        rule.rule_config = rule_config
        rule.is_active = is_active
        return await self.rule_repo.update(rule)

    async def delete_rule(self, rule_id: uuid.UUID) -> bool:
        return await self.rule_repo.delete(rule_id)

    async def reorder_rules(self, rule_orders: list[dict]) -> bool:
        await self.rule_repo.update_order(rule_orders)
        return True

    def _rule_to_dict(self, rule: ChunkingRule) -> dict:
        return {
            "id": str(rule.id),
            "name": rule.name,
            "description": rule.description,
            "rule_type": rule.rule_type,
            "rule_config": rule.rule_config,
            "is_active": rule.is_active,
            "sort_order": rule.sort_order,
            "created_at": rule.created_at.isoformat() if rule.created_at else None,
            "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
        }
