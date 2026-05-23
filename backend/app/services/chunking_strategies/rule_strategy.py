import re
from .base import BaseChunkingStrategy, Chunk


class HeadingChunkingStrategy(BaseChunkingStrategy):
    strategy_name = "heading"

    async def chunk(self, text: str, config: dict) -> list[Chunk]:
        levels = config.get("levels", [1, 2, 3])
        pattern = "|".join([r"^#{%d}\s+.+$" % l for l in levels])
        matches = list(re.finditer(pattern, text, re.MULTILINE))

        chunks = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(Chunk(
                    index=i,
                    text=chunk_text,
                    start_pos=start,
                    end_pos=end,
                    metadata={"heading": match.group()},
                ))
        return chunks


class ParagraphChunkingStrategy(BaseChunkingStrategy):
    strategy_name = "paragraph"

    async def chunk(self, text: str, config: dict) -> list[Chunk]:
        min_length = config.get("min_length", 50)
        paragraphs = re.split(r"\n\s*\n", text)

        chunks = []
        current_pos = 0
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if len(para) >= min_length:
                start = text.find(para, current_pos)
                if start == -1:
                    start = current_pos
                end = start + len(para)
                chunks.append(Chunk(
                    index=i,
                    text=para,
                    start_pos=start,
                    end_pos=end,
                    metadata={},
                ))
                current_pos = end

        return chunks


class LengthChunkingStrategy(BaseChunkingStrategy):
    strategy_name = "length"

    async def chunk(self, text: str, config: dict) -> list[Chunk]:
        max_length = config.get("max_length", 5000)
        overlap = config.get("overlap", 500)

        chunks = []
        start = 0
        i = 0
        while start < len(text):
            end = min(start + max_length, len(text))
            chunk_text = text[start:end]
            if chunk_text:
                chunks.append(Chunk(
                    index=i,
                    text=chunk_text,
                    start_pos=start,
                    end_pos=end,
                    metadata={"length_based": True},
                ))
            start = end - overlap
            i += 1

        return chunks
