import uuid
import re
import logging
from app.services.storage_service import StorageService
from app.services.chunking_strategies import (
    HeadingChunkingStrategy,
    ParagraphChunkingStrategy,
    LengthChunkingStrategy,
    Chunk,
)
from app.services.vector_service import VectorService
from app.dal.repositories import (
    WikiFileRepository,
    WikiChunkRepository,
    ChunkingRuleRepository,
)

logger = logging.getLogger(__name__)


class DocumentProcessorService:
    """文档处理服务：负责文档解析、切片、向量化"""

    def __init__(
        self,
        storage_service: StorageService,
        vector_service: VectorService,
        file_repo: WikiFileRepository,
        chunk_repo: WikiChunkRepository,
        rule_repo: ChunkingRuleRepository,
    ):
        self.storage_service = storage_service
        self.vector_service = vector_service
        self.file_repo = file_repo
        self.chunk_repo = chunk_repo
        self.rule_repo = rule_repo

    def _clean_markdown(self, content: str) -> str:
        content = re.sub(r"!\[.*?\]\(.*?\)", "", content)
        content = re.sub(r"\|.*?\|[\s-]+", lambda m: m.group().split("\n")[0] + "\n", content)
        content = re.sub(r"<[^>]+>", "", content)
        return content.strip()

    async def process_document(self, page_id: uuid.UUID, file_id: uuid.UUID, page_tags: list[str] = None):
        try:
            file = await self.file_repo.get_by_id(file_id)
            if not file:
                raise ValueError(f"File not found: {file_id}")

            content = await self.storage_service.download(file.file_path)
            text = content.decode("utf-8")

            cleaned_text = self._clean_markdown(text)

            rules = await self.rule_repo.get_active_rules()
            if not rules:
                rules = [type("obj", (object,), {
                    "rule_type": "paragraph",
                    "rule_config": {"min_length": 50},
                })]

            all_chunks = []
            for rule in rules:
                if rule.rule_type == "heading":
                    strategy = HeadingChunkingStrategy()
                elif rule.rule_type == "paragraph":
                    strategy = ParagraphChunkingStrategy()
                elif rule.rule_type == "length":
                    strategy = LengthChunkingStrategy()
                else:
                    continue

                chunks = await strategy.chunk(cleaned_text, rule.rule_config)
                all_chunks.extend(chunks)

            texts = [chunk.text for chunk in all_chunks]
            embeddings = await self.vector_service.generate_embeddings(texts)

            for i, (chunk, embedding) in enumerate(zip(all_chunks, embeddings)):
                vector_id = await self.vector_service.insert(
                    texts=[chunk.text],
                    embeddings=[embedding],
                    user_ids=["system"],
                    dept_ids=[None],
                    sensitivities=["public"],
                    extra_fields={
                        "file_id": str(file_id),
                        "chunk_index": i,
                        "tags": page_tags or [],
                    },
                )

                chunk_record = type("obj", (object,), {
                    "file_id": file_id,
                    "chunk_index": i,
                    "start_pos": chunk.start_pos,
                    "end_pos": chunk.end_pos,
                    "text_preview": chunk.text[:200],
                    "vector_id": vector_id[0],
                })
                await self.chunk_repo.create(chunk_record)

            return True, len(all_chunks)

        except Exception as e:
            logger.error(f"Failed to process document {file_id}: {e}")
            return False, str(e)
