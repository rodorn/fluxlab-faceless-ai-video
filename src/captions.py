"""Napisy: podzial scenariusza na segmenty czasowe i generacja .srt.

Deterministyczne, bez API. Czas trwania segmentu szacowany z liczby slow
i tempa mowy (WPM), z podloga minimalnej dlugosci.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import Script

DEFAULT_WPM = 150  # slow na minute (polski lektor, spokojne tempo)
MIN_SEGMENT_SEC = 1.5
GAP_SEC = 0.15  # krotka przerwa miedzy segmentami


@dataclass
class TimedSegment:
    index: int
    text: str
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


def estimate_duration(text: str, wpm: int = DEFAULT_WPM) -> float:
    """Szacowany czas wypowiedzenia tekstu w sekundach."""
    words = max(1, len(text.split()))
    seconds = words / wpm * 60.0
    return max(MIN_SEGMENT_SEC, round(seconds, 3))


def build_timeline(
    segments: List[str], wpm: int = DEFAULT_WPM, gap: float = GAP_SEC
) -> List[TimedSegment]:
    """Buduje osie czasu dla listy segmentow tekstu."""
    timeline: List[TimedSegment] = []
    cursor = 0.0
    for i, text in enumerate(segments, start=1):
        dur = estimate_duration(text, wpm)
        start = cursor
        end = start + dur
        timeline.append(TimedSegment(index=i, text=text, start=start, end=end))
        cursor = end + gap
    return timeline


def total_duration(
    segments: List[str], wpm: int = DEFAULT_WPM, gap: float = GAP_SEC
) -> float:
    """Calkowita dlugosc materialu (bez koncowego gapa)."""
    tl = build_timeline(segments, wpm, gap)
    if not tl:
        return 0.0
    return round(tl[-1].end, 3)


def _fmt_ts(seconds: float) -> str:
    """Formatuje sekundy do znacznika SRT HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0.0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(segments: List[str], wpm: int = DEFAULT_WPM, gap: float = GAP_SEC) -> str:
    """Buduje zawartosc pliku .srt z listy segmentow."""
    timeline = build_timeline(segments, wpm, gap)
    blocks = []
    for seg in timeline:
        blocks.append(
            f"{seg.index}\n{_fmt_ts(seg.start)} --> {_fmt_ts(seg.end)}\n{seg.text}\n"
        )
    return "\n".join(blocks)


def write_srt(script: Script, path: str, wpm: int = DEFAULT_WPM) -> str:
    """Zapisuje .srt dla scenariusza. Zwraca sciezke."""
    content = build_srt(script.segments(), wpm=wpm)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path
