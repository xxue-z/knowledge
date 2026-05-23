from .base import BaseChunkingStrategy, Chunk


class LLMChunkingStrategy(BaseChunkingStrategy):
    strategy_name = "llm"

    def __init__(self, llm_service):
        self.llm_service = llm_service

    async def chunk(self, text: str, config: dict) -> list[Chunk]:
        max_chunks = config.get("max_chunks", 10)
        prompt = f"""请将以下文本分割成语义完整的片段，每个片段应该是一个独立的段落或主题。

要求：
1. 每个片段应该尽可能语义完整
2. 返回 {max_chunks} 个左右的片段
3. 每个片段用 | 分隔
4. 只返回片段，不要其他内容

文本：
{text[:10000]}
"""
        try:
            response = await self.llm_service.chat([{"role": "user", "content": prompt}])
            content = response.get("content", "")

            parts = content.split("|")
            chunks = []
            current_pos = 0

            for i, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue
                idx = text.find(part, current_pos)
                if idx == -1:
                    idx = current_pos
                end = idx + len(part)
                chunks.append(Chunk(
                    index=i,
                    text=part,
                    start_pos=idx,
                    end_pos=end,
                    metadata={"llm_generated": True},
                ))
                current_pos = end

            return chunks[:max_chunks]
        except Exception:
            return []
