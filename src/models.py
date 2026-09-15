"""Wspolne struktury danych dla pipeline'u."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Script:
    """Scenariusz wideo: hook, sceny, CTA."""

    title: str
    hook: str
    scenes: List[str] = field(default_factory=list)
    cta: str = ""

    def segments(self) -> List[str]:
        """Zwraca liste segmentow tekstu w kolejnosci narracji."""
        parts = [self.hook, *self.scenes, self.cta]
        return [p.strip() for p in parts if p and p.strip()]

    def full_text(self) -> str:
        return " ".join(self.segments())
