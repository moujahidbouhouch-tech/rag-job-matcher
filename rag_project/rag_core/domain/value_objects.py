from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class JobId:
    value: UUID


@dataclass(frozen=True)
class ChunkId:
    value: UUID
