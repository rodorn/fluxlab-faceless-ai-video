"""Montaz FFmpeg: tlo + lektor + wypalone napisy + muzyka -> pionowy MP4 1080x1920.

Tryb demo realnie produkuje plik MP4:
- tlo: jednolity kolor (lub podane obrazy jako pokaz slajdow),
- audio: lektor (voice.py),
- muzyka: placeholder (cichy sinus zmiksowany pod lektorem),
- napisy: wypalone z pliku .srt (filtr subtitles).
"""

from __future__ import annotations

import logging
import os
import subprocess
from typing import List, Optional

log = logging.getLogger(__name__)

WIDTH = 1080
HEIGHT = 1920
FPS = 30
BG_COLOR = "0x0f1020"  # ciemny granat
MUSIC_VOLUME = 0.06


def _escape_subtitles_path(path: str) -> str:
    """Escapuje sciezke dla filtra subtitles ffmpeg."""
    p = os.path.abspath(path)
    p = p.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")
    return p


def build_ffmpeg_command(
    audio_path: str,
    srt_path: str,
    out_path: str,
    duration: float,
    images: Optional[List[str]] = None,
    bg_color: str = BG_COLOR,
    music_path: Optional[str] = None,
    width: int = WIDTH,
    height: int = HEIGHT,
    fps: int = FPS,
) -> List[str]:
    """Buduje liste argumentow komendy ffmpeg (testowalne, bez uruchamiania)."""
    cmd: List[str] = ["ffmpeg", "-y"]
    filter_parts: List[str] = []
    n_inputs = 0

    if images:
        seg = max(0.5, duration / len(images))
        for img in images:
            cmd += ["-loop", "1", "-t", f"{seg:.3f}", "-i", img]
        labels = []
        for i in range(len(images)):
            filter_parts.append(
                f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},setsar=1,fps={fps}[img{i}]"
            )
            labels.append(f"[img{i}]")
        filter_parts.append(f"{''.join(labels)}concat=n={len(images)}:v=1:a=0[bg]")
        n_inputs = len(images)
    else:
        cmd += [
            "-f",
            "lavfi",
            "-t",
            f"{duration:.3f}",
            "-i",
            f"color=c={bg_color}:s={width}x{height}:r={fps}",
        ]
        filter_parts.append("[0:v]setsar=1[bg]")
        n_inputs = 1

    voice_idx = n_inputs
    cmd += ["-i", audio_path]

    music_idx = voice_idx + 1
    if music_path:
        cmd += ["-i", music_path]
    else:
        cmd += [
            "-f",
            "lavfi",
            "-t",
            f"{duration:.3f}",
            "-i",
            "sine=frequency=220:sample_rate=44100",
        ]

    sub = _escape_subtitles_path(srt_path)
    style = "FontSize=16,PrimaryColour=&H00FFFFFF,Outline=2,MarginV=120,Alignment=2"
    filter_parts.append(f"[bg]subtitles='{sub}':force_style='{style}'[v]")
    filter_parts.append(f"[{music_idx}:a]volume={MUSIC_VOLUME}[music]")
    filter_parts.append(
        f"[{voice_idx}:a][music]amix=inputs=2:duration=first:dropout_transition=0[a]"
    )

    cmd += [
        "-filter_complex",
        ";".join(filter_parts),
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-profile:v",
        "high",
        "-r",
        str(fps),
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-shortest",
        "-t",
        f"{duration:.3f}",
        out_path,
    ]
    return cmd


def assemble(
    audio_path: str,
    srt_path: str,
    duration: float,
    out_path: str = "out/video.mp4",
    images: Optional[List[str]] = None,
    music_path: Optional[str] = None,
) -> str:
    """Uruchamia ffmpeg i zwraca sciezke do gotowego MP4."""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    cmd = build_ffmpeg_command(
        audio_path=audio_path,
        srt_path=srt_path,
        out_path=out_path,
        duration=duration,
        images=images,
        music_path=music_path,
    )
    log.info("assemble: ffmpeg %s", " ".join(cmd))
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path
