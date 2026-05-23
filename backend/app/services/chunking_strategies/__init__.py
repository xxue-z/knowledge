from .base import BaseChunkingStrategy, Chunk
from .rule_strategy import HeadingChunkingStrategy, ParagraphChunkingStrategy, LengthChunkingStrategy

STRATEGY_MAP = {
    "heading": HeadingChunkingStrategy,
    "paragraph": ParagraphChunkingStrategy,
    "length": LengthChunkingStrategy,
}

__all__ = [
    "BaseChunkingStrategy",
    "Chunk",
    "HeadingChunkingStrategy",
    "ParagraphChunkingStrategy",
    "LengthChunkingStrategy",
    "STRATEGY_MAP",
]
