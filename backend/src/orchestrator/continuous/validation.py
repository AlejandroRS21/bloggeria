"""Validation helpers for continuous publishing output."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable


@dataclass
class DraftValidator:
    """Validates draft completeness and redundancy against recent history."""

    redundancy_threshold: float = 0.8

    def validate_minimum_fields(self, title: str, excerpt: str, body: str, published_at: str) -> bool:
        """Validate mandatory fields before publishing."""
        return bool(title.strip() and excerpt.strip() and body.strip() and str(published_at).strip())

    def similarity(self, left: str, right: str) -> float:
        """Compute normalized text similarity in [0, 1]."""
        return SequenceMatcher(None, left or "", right or "").ratio()

    def is_redundant(self, candidate_text: str, recent_texts: Iterable[str]) -> bool:
        """Check if candidate is redundant against any recent text."""
        return any(self.similarity(candidate_text, txt) >= self.redundancy_threshold for txt in recent_texts)
