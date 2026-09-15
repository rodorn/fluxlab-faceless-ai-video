#!/usr/bin/env python3
"""Orkiestracja pipeline'u faceless AI video.

Kroki: script -> voice -> captions -> assemble -> publish (dry-run).
Uruchomienie demo (bez kluczy):  python run.py
Publikacja realna:               python run.py --publish   (wymaga tokenow w env)
"""

from __future__ import annotations

import argparse
import logging
import os

from src.assemble import assemble
from src.captions import total_duration, write_srt
from src.publish import publish
from src.script_gen import generate_script
from src.voice import synthesize

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("run")

OUT_DIR = "out"


def main() -> None:
    parser = argparse.ArgumentParser(description="FluxLab faceless AI video pipeline")
    parser.add_argument("--topic", default="porady stylizacyjne dla mezczyzn")
    parser.add_argument(
        "--publish", action="store_true", help="realna publikacja (domyslnie dry-run)"
    )
    parser.add_argument(
        "--images", nargs="*", default=None, help="opcjonalne obrazy tla"
    )
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    log.info("== 1/5 Scenariusz ==")
    script = generate_script(args.topic)
    log.info("Tytul: %s", script.title)
    log.info("Segmentow: %d", len(script.segments()))

    log.info("== 2/5 Lektor ==")
    audio_path, duration = synthesize(
        script, out_path=os.path.join(OUT_DIR, "voice.mp3")
    )
    log.info("Audio: %s (%.2fs)", audio_path, duration)

    log.info("== 3/5 Napisy (SRT) ==")
    srt_path = write_srt(script, os.path.join(OUT_DIR, "captions.srt"))
    log.info("SRT: %s", srt_path)

    log.info("== 4/5 Montaz (MP4 1080x1920) ==")
    video_path = assemble(
        audio_path=audio_path,
        srt_path=srt_path,
        duration=total_duration(script.segments()),
        out_path=os.path.join(OUT_DIR, "video.mp4"),
        images=args.images,
    )
    size = os.path.getsize(video_path)
    log.info("MP4: %s (%d bajtow, %.1f KB)", video_path, size, size / 1024)

    log.info("== 5/5 Publikacja ==")
    caption = f"{script.title}\n\n{script.cta}"
    results = publish(video_path, caption, dry_run=not args.publish)
    for r in results:
        log.info("publish[%s]: %s (%s)", r.platform, r.status, r.detail)

    print("\n=== PODSUMOWANIE ===")
    print(f"MP4:  {os.path.abspath(video_path)}  ({size} bajtow, {size / 1024:.1f} KB)")
    print(f"SRT:  {os.path.abspath(srt_path)}")
    print(f"AUDIO:{os.path.abspath(audio_path)}  ({duration:.2f}s)")
    print("PUBLISH:", ", ".join(f"{r.platform}={r.status}" for r in results))


if __name__ == "__main__":
    main()
