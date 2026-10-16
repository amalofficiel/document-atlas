"""One chunk identity shared by vector, keyword and fused retrieval."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchHit:
    id: str
    payload: dict
    score: float = 0.0
    scores: dict = field(default_factory=dict)
    ranks: dict = field(default_factory=dict)
