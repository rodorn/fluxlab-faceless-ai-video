"""Testy generatora scenariusza (tryb demo)."""

from src.script_gen import DEMO_SCRIPT, generate_script


def test_demo_script_shape(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    s = generate_script("cokolwiek")
    assert s is DEMO_SCRIPT
    assert s.hook
    assert len(s.scenes) == 5
    assert s.cta
    # hook + 5 scen + cta = 7 segmentow
    assert len(s.segments()) == 7
