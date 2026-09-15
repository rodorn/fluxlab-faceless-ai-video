"""Lektor po polsku.

Tryb realny: ElevenLabs API (ELEVENLABS_API_KEY) -> plik MP3/WAV.
Tryb demo (brak klucza): placeholder audio (cisza) o dlugosci dopasowanej
do tekstu, generowany przez ffmpeg (anullsrc). Dzieki temu montaz dziala
bez platnych kluczy.
"""

from __future__ import annotations

import logging
import os
import subprocess

from .captions import total_duration
from .models import Script

log = logging.getLogger(__name__)

DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs "Rachel" (przyklad)


def _synthesize_elevenlabs(text: str, out_path: str, api_key: str) -> str:
    import requests  # import lokalny, opcjonalna zaleznosc

    voice_id = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)
    model_id = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    resp = requests.post(
        url,
        headers={"xi-api-key": api_key, "accept": "audio/mpeg"},
        json={
            "text": text,
            "model_id": model_id,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        },
        timeout=120,
    )
    resp.raise_for_status()
    with open(out_path, "wb") as fh:
        fh.write(resp.content)
    return out_path


def _silent_placeholder(duration: float, out_path: str) -> str:
    """Generuje cichy plik audio o zadanej dlugosci przez ffmpeg."""
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t",
        f"{duration:.3f}",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "128k",
        out_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def synthesize(script: Script, out_path: str = "out/voice.mp3") -> tuple[str, float]:
    """Tworzy lektora. Zwraca (sciezka, dlugosc_w_sekundach).

    Bez ELEVENLABS_API_KEY generuje cichy placeholder o dlugosci dopasowanej
    do tekstu scenariusza.
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    segments = script.segments()
    duration = total_duration(segments)
    api_key = os.getenv("ELEVENLABS_API_KEY")

    if api_key:
        log.info("voice: uzywam ElevenLabs")
        _synthesize_elevenlabs(script.full_text(), out_path, api_key)
        return out_path, duration

    log.info(
        "voice: tryb demo (brak ELEVENLABS_API_KEY), generuje cichy placeholder %.2fs",
        duration,
    )
    _silent_placeholder(duration, out_path)
    return out_path, duration
