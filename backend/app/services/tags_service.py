import uuid
from app.dal.repositories import WikiTagRepository, WikiPageRepository
from app.models.wiki_storage import WikiTag


class TagsService:
    """标签管理服务"""

    def __init__(self, tag_repo: WikiTagRepository, page_repo: WikiPageRepository):
        self.tag_repo = tag_repo
        self.page_repo = page_repo

    async def list_tags(self) -> list[dict]:
        tags = await self.tag_repo.get_all_with_children()
        return [self._tag_to_dict(t) for t in tags]

    async def get_tag_tree(self) -> list[dict]:
        root_tags = await self.tag_repo.get_root_tags()
        result = []
        for tag in root_tags:
            result.append(await self._build_tree(tag))
        return result

    async def _build_tree(self, tag: WikiTag) -> dict:
        children = await self.tag_repo.get_children(tag.id)
        return {
            "id": str(tag.id),
            "name": tag.name,
            "color": tag.color,
            "description": tag.description,
            "children": [await self._build_tree(c) for c in children],
        }

    async def create_tag(self, name: str, color: str, description: str, parent_id: uuid.UUID | None, created_by: str) -> WikiTag:
        existing = await self.tag_repo.get_by_name(name)
        if existing:
            raise ValueError(f"Tag with name '{name}' already exists")

        tag = WikiTag(
            name=name,
            color=color,
            description=description,
            parent_id=parent_id,
            created_by=created_by,
        )
        return await self.tag_repo.create(tag)

    async def update_tag(self, tag_id: uuid.UUID, name: str, color: str, description: str, parent_id: uuid.UUID | None) -> WikiTag | None:
        tag = await self.tag_repo.get_by_id(tag_id)
        if not tag:
            return None

        tag.name = name
        tag.color = color
        tag.description = description
        tag.parent_id = parent_id
        return await self.tag_repo.update(tag)

    async def delete_tag(self, tag_id: uuid.UUID) -> bool:
        return await self.tag_repo.delete(tag_id)

    async def add_tag_to_page(self, page_id: uuid.UUID, tag_id: uuid.UUID) -> bool:
        page = await self.page_repo.get_by_id(page_id)
        tag = await self.tag_repo.get_by_id(tag_id)
        if not page or not tag:
            return False

        if tag not in page.tags:
            page.tags.append(tag)
            await self.page_repo.update(page)
        return True

    async def remove_tag_from_page(self, page_id: uuid.UUID, tag_id: uuid.UUID) -> bool:
        page = await self.page_repo.get_by_id(page_id)
        tag = await self.tag_repo.get_by_id(tag_id)
        if not page or not tag:
            return False

        if tag in page.tags:
            page.tags.remove(tag)
            await self.page_repo.update(page)
        return True

    def _tag_to_dict(self, tag: WikiTag) -> dict:
        return {
            "id": str(tag.id),
            "name": tag.name,
            "color": tag.color,
            "description": tag.description,
            "parent_id": str(tag.parent_id) if tag.parent_id else None,
            "created_by": tag.created_by,
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
        }
