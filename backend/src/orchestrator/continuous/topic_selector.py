"""Topic selection for continuous publishing with recency and diversity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Sequence


@dataclass
class TopicCandidate:
    """Candidate topic with metadata and scoring for selection."""

    title: str
    category: str
    source: str
    published_at: Optional[datetime] = None
    recency_score: float = 0.0


@dataclass
class TopicSelector:
    """Selects best topic balancing recency and category diversity."""

    recency_window_hours: int = 72
    category_cooldown: int = 1
    _recent_categories: List[str] = field(default_factory=list)

    def score_recency(self, published_at: Optional[datetime], now: Optional[datetime] = None) -> float:
        """Score recency from 0 to 1 within configured window."""
        if not published_at:
            return 0.0
        current = now or datetime.now(timezone.utc)
        age_hours = max((current - published_at).total_seconds() / 3600.0, 0.0)
        if age_hours >= self.recency_window_hours:
            return 0.0
        return max(0.0, 1.0 - (age_hours / self.recency_window_hours))

    def select(self, candidates: Sequence[TopicCandidate]) -> Optional[TopicCandidate]:
        """Pick highest-score candidate, preferring category diversity."""
        if not candidates:
            return None

        scored: List[TopicCandidate] = []
        for candidate in candidates:
            candidate.recency_score = self.score_recency(candidate.published_at)
            diversity_boost = 0.15 if candidate.category not in self._recent_categories[-self.category_cooldown :] else 0.0
            candidate.recency_score += diversity_boost
            scored.append(candidate)

        selected = sorted(scored, key=lambda c: c.recency_score, reverse=True)[0]
        self._recent_categories.append(selected.category)
        return selected
