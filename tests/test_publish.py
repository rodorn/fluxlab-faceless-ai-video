"""Testy dry-run publikacji i retry."""

import src.publish as publish_mod
from src.publish import PublishResult, _retry, publish


def test_dry_run_uploads_nothing(monkeypatch):
    monkeypatch.delenv("TIKTOK_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("YOUTUBE_ACCESS_TOKEN", raising=False)
    results = publish("out/video.mp4", "opis", dry_run=True)
    assert len(results) == 2
    assert all(r.status == "dry-run" for r in results)
    platforms = {r.platform for r in results}
    assert platforms == {"tiktok", "youtube_shorts"}


def test_missing_token_falls_back_to_dry_run(monkeypatch):
    monkeypatch.delenv("TIKTOK_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("YOUTUBE_ACCESS_TOKEN", raising=False)
    # nawet z dry_run=False, brak tokenow -> nic nie wysyla
    results = publish("out/video.mp4", "opis", dry_run=False)
    assert all(r.status == "dry-run" for r in results)


def test_retry_succeeds_after_failures():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("chwilowy blad")
        return PublishResult(platform="tiktok", status="uploaded")

    res = _retry(flaky, "tiktok", sleep=lambda s: None)
    assert res.status == "uploaded"
    assert calls["n"] == 3


def test_retry_gives_up_and_reports_error():
    def always_fail():
        raise RuntimeError("trwaly blad")

    res = _retry(always_fail, "youtube_shorts", sleep=lambda s: None)
    assert res.status == "error"
    assert "trwaly blad" in res.detail


def test_real_upload_called_with_token(monkeypatch):
    monkeypatch.setenv("TIKTOK_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("YOUTUBE_ACCESS_TOKEN", "tok")
    seen = []

    def fake_tiktok(video_path, caption, token):
        seen.append("tiktok")
        return PublishResult(platform="tiktok", status="uploaded")

    def fake_youtube(video_path, caption, token):
        seen.append("youtube")
        return PublishResult(platform="youtube_shorts", status="uploaded")

    monkeypatch.setattr(publish_mod, "_upload_tiktok", fake_tiktok)
    monkeypatch.setattr(publish_mod, "_upload_youtube", fake_youtube)
    results = publish("out/video.mp4", "opis", dry_run=False)
    assert seen == ["tiktok", "youtube"]
    assert all(r.status == "uploaded" for r in results)
