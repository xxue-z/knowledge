from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Chunk:
    index: int
    text: str
    start_pos: int
    end_pos: int
    metadata: dict = None


class BaseChunkingStrategy(ABC):
    """切片策略抽象基类"""

    strategy_name: str = ""

    @abstractmethod
    async def chunk(self, text: str, config: dict) -> list[Chunk]:
        pass
