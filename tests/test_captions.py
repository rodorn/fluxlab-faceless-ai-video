"""Testy podzialu napisow i generacji SRT."""

import re

from src.captions import (
    MIN_SEGMENT_SEC,
    build_srt,
    build_timeline,
    estimate_duration,
    total_duration,
    _fmt_ts,
)
from src.models import Script


def test_estimate_duration_min_floor():
    assert estimate_duration("krotko") == MIN_SEGMENT_SEC


def test_estimate_duration_scales_with_words():
    short = estimate_duration(" ".join(["slowo"] * 10))
    long = estimate_duration(" ".join(["slowo"] * 100))
    assert long > short


def test_timeline_monotonic_and_gapped():
    segs = ["pierwszy segment tekstu", "drugi segment", "trzeci segment tutaj"]
    tl = build_timeline(segs)
    assert len(tl) == 3
    for a, b in zip(tl, tl[1:]):
        assert b.start > a.end  # jest gap
        assert a.start < a.end
    assert tl[0].start == 0.0


def test_fmt_ts_format():
    assert _fmt_ts(0) == "00:00:00,000"
    assert _fmt_ts(3661.5) == "01:01:01,500"


def test_build_srt_structure():
    segs = ["hook zdanie", "scena jeden", "cta koncowe"]
    srt = build_srt(segs)
    # numery blokow 1..3
    assert srt.startswith("1\n")
    assert "\n2\n" in srt
    assert "\n3\n" in srt
    # kazdy blok ma znacznik czasu z strzalka
    arrows = re.findall(r"\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}", srt)
    assert len(arrows) == 3
    # tekst obecny
    assert "hook zdanie" in srt


def test_total_duration_matches_last_segment_end():
    segs = ["a b c", "d e f g"]
    tl = build_timeline(segs)
    assert total_duration(segs) == round(tl[-1].end, 3)


def test_script_segments_order():
    s = Script(title="t", hook="H", scenes=["S1", "S2"], cta="C")
    assert s.segments() == ["H", "S1", "S2", "C"]
