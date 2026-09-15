"""Szkielet publikacji na TikTok i YouTube Shorts.

Tryb realny wymaga tokenow OAuth w env:
- TikTok:  TIKTOK_ACCESS_TOKEN (Content Posting API)
- YouTube: YOUTUBE_ACCESS_TOKEN (YouTube Data API v3, upload)

Tryb demo (dry-run, brak tokenow LUB dry_run=True): tylko loguje "would upload",
nic nie publikuje. Publikacja realna ma retry z wykladniczym backoffem.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Callable, Optional

log = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_BASE = 2.0


@dataclass
class PublishResult:
    platform: str
    status: str  # "dry-run" | "uploaded" | "error"
    detail: str = ""


def _retry(
    fn: Callable[[], PublishResult], platform: str, sleep=time.sleep
) -> PublishResult:
    last = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - szkielet, logujemy i ponawiamy
            last = str(exc)
            log.warning(
                "%s: proba %d/%d nieudana: %s", platform, attempt, MAX_RETRIES, last
            )
            if attempt < MAX_RETRIES:
                sleep(BACKOFF_BASE**attempt)
    return PublishResult(platform=platform, status="error", detail=last)


def _upload_tiktok(video_path: str, caption: str, token: str) -> PublishResult:
    import requests  # import lokalny, opcjonalna zaleznosc

    # Szkielet: inicjacja publikacji przez TikTok Content Posting API.
    resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "post_info": {"title": caption, "privacy_level": "SELF_ONLY"},
            "source_info": {"source": "FILE_UPLOAD"},
        },
        timeout=60,
    )
    resp.raise_for_status()
    return PublishResult(platform="tiktok", status="uploaded", detail=resp.text[:200])


def _upload_youtube(video_path: str, caption: str, token: str) -> PublishResult:
    import requests  # import lokalny, opcjonalna zaleznosc

    # Szkielet: resumable upload do YouTube Data API v3 (videos.insert).
    resp = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "snippet": {
                "title": caption[:100],
                "description": caption,
                "categoryId": "22",
            },
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False},
        },
        timeout=60,
    )
    resp.raise_for_status()
    return PublishResult(
        platform="youtube_shorts", status="uploaded", detail="upload session ok"
    )


def publish(
    video_path: str,
    caption: str,
    dry_run: bool = True,
    platforms: Optional[list[str]] = None,
) -> list[PublishResult]:
    """Publikuje wideo. Domyslnie dry-run (nic nie wysyla)."""
    platforms = platforms or ["tiktok", "youtube_shorts"]
    tiktok_token = os.getenv("TIKTOK_ACCESS_TOKEN")
    youtube_token = os.getenv("YOUTUBE_ACCESS_TOKEN")
    results: list[PublishResult] = []

    for platform in platforms:
        token = tiktok_token if platform == "tiktok" else youtube_token
        if dry_run or not token:
            reason = "dry_run=True" if dry_run else "brak tokenu"
            log.info(
                "publish[%s]: would upload %s (%s), caption=%r",
                platform,
                video_path,
                reason,
                caption[:60],
            )
            results.append(
                PublishResult(platform=platform, status="dry-run", detail=reason)
            )
            continue

        if platform == "tiktok":
            results.append(
                _retry(lambda: _upload_tiktok(video_path, caption, token), platform)
            )
        elif platform == "youtube_shorts":
            results.append(
                _retry(lambda: _upload_youtube(video_path, caption, token), platform)
            )
        else:
            results.append(
                PublishResult(
                    platform=platform, status="error", detail="nieznana platforma"
                )
            )

    return results
