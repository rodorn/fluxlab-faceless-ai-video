#!/usr/bin/env python3
"""Buduje klip demo TomStyl z lektorem ElevenLabs (multilingual_v2, PL).

Per-zdanie TTS ElevenLabs -> realne czasy -> synchro napisy -> montaz premium.
Uruchomienie: ELEVENLABS_API_KEY=... python3 build_demo_11.py
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")

VOICE_ID = os.getenv(
    "ELEVENLABS_VOICE_ID", "zzBTsLBFM6AOJtkr1e9b"
)  # Pawel Pro - Polish
MODEL_ID = "eleven_multilingual_v2"
API_KEY = os.environ["ELEVENLABS_API_KEY"]
VOICE_SETTINGS = {
    "stability": 0.4,
    "similarity_boost": 0.75,
    "style": 0.3,
    "use_speaker_boost": True,
}

GAP = 0.14  # cisza miedzy zdaniami (s)
MAX_CHUNK_WORDS = 4  # max slow na jeden napis (styl shorts)
TARGET_MAX = 44.0  # gorna granica dlugosci klipu (s)

LINES = [
    "Ten samochód tracił pieniądze przy każdej sprzedaży. I to miliony dolarów.",
    "Bugatti Veyron kosztował ponad milion euro, a mimo to koncern Volkswagena dokładał do każdego egzemplarza.",
    "Szacuje się, że przy każdym sprzedanym aucie firma traciła nawet pięć milionów dolarów.",
    "Dlaczego? Bo Veyron miał tysiąc koni mechanicznych i rozpędzał się do ponad czterystu kilometrów na godzinę.",
    "Przy tej prędkości opony wytrzymywały tylko piętnaście minut, a komplet kosztował tyle, co nowy samochód.",
    "Volkswagen nie budował go dla zysku. Zbudował go, żeby udowodnić całemu światu, że po prostu potrafi.",
    "Czasem najdroższy projekt w historii motoryzacji to nie biznes. To czysta duma inżynierów.",
]


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def probe_dur(path: str) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            path,
        ]
    )
    return float(out.decode().strip())


def tts(text: str, out_mp3: str):
    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        f"?output_format=mp3_44100_128"
    )
    body = json.dumps(
        {"text": text, "model_id": MODEL_ID, "voice_settings": VOICE_SETTINGS}
    ).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "xi-api-key": API_KEY,
            "Content-Type": "application/json",
            "accept": "audio/mpeg",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if len(data) < 1000:
        raise RuntimeError(f"Zbyt male audio ({len(data)}B) dla: {text[:40]}")
    with open(out_mp3, "wb") as fh:
        fh.write(data)


def fmt_ts(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def chunk_words(text: str, n: int):
    words = text.replace("\n", " ").split()
    return [" ".join(words[i : i + n]) for i in range(0, len(words), n)]


def main():
    os.makedirs(OUT, exist_ok=True)
    parts = os.path.join(OUT, "parts11")
    os.makedirs(parts, exist_ok=True)

    # 1) synteza per-zdanie ElevenLabs + pomiar realnej dlugosci
    seg = []  # (wav, text, dur)
    for i, line in enumerate(LINES):
        mp3 = os.path.join(parts, f"e{i:02d}.mp3")
        wav = os.path.join(parts, f"e{i:02d}.wav")
        tts(line, mp3)
        run(["ffmpeg", "-y", "-i", mp3, "-ar", "44100", "-ac", "1", wav])
        seg.append((wav, line, probe_dur(wav)))

    raw_total = sum(d for _, _, d in seg) + GAP * (len(seg) - 1)
    tempo = max(1.0, raw_total / TARGET_MAX)
    print(f"RAW_TOTAL={raw_total:.3f} TEMPO={tempo:.4f}")

    # 2) sklej w jeden tor z cisza miedzy zdaniami
    concat_in = []
    for wav, _, _ in seg:
        concat_in += ["-i", wav]
    silence = "aevalsrc=0:d=%.3f:s=44100" % GAP
    fc, labels = [], []
    for k in range(len(seg)):
        labels.append(f"[{k}:a]")
        if k < len(seg) - 1:
            fc.append(f"{silence}[s{k}]")
            labels.append(f"[s{k}]")
    fc.append(f"{''.join(labels)}concat=n={len(labels)}:v=0:a=1[cat]")
    voice_cat = os.path.join(OUT, "voice11_cat.wav")
    run(
        [
            "ffmpeg",
            "-y",
            *concat_in,
            "-filter_complex",
            ";".join(fc),
            "-map",
            "[cat]",
            voice_cat,
        ]
    )

    # 3) tempo (jesli potrzebny) -> voice_11.wav + voice_11.mp3
    voice_wav = os.path.join(OUT, "voice_11.wav")
    af = f"atempo={tempo:.4f}" if tempo > 1.001 else "anull"
    run(["ffmpeg", "-y", "-i", voice_cat, "-af", af, "-ar", "44100", voice_wav])
    voice_mp3 = os.path.join(OUT, "voice_11.mp3")
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            voice_wav,
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            voice_mp3,
        ]
    )
    total = probe_dur(voice_wav)
    print(f"VOICE_TOTAL={total:.3f}")

    # 4) SRT z realnych czasow (po tempie), krotkie frazy UPPERCASE
    srt = os.path.join(OUT, "captions_11.srt")
    cursor, n, blocks = 0.0, 0, []
    for _, text, raw_d in seg:
        d = raw_d / tempo
        chunks = chunk_words(text, MAX_CHUNK_WORDS)
        wtot = sum(len(c.split()) for c in chunks)
        cstart = cursor
        for c in chunks:
            cend = cstart + d * (len(c.split()) / wtot)
            n += 1
            blocks.append(f"{n}\n{fmt_ts(cstart)} --> {fmt_ts(cend)}\n{c.upper()}\n")
            cstart = cend
        cursor += d + GAP / tempo
    with open(srt, "w", encoding="utf-8") as fh:
        fh.write("\n".join(blocks))

    # 5) muzyka: delikatny ambient o dlugosci klipu
    music = os.path.join(OUT, "music_11.wav")
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=110:duration={total:.3f}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=220:duration={total:.3f}",
            "-filter_complex",
            "[0:a]volume=0.5[a0];[1:a]volume=0.25[a1];[a0][a1]amix=inputs=2,"
            "tremolo=f=0.15:d=0.4,aformat=channel_layouts=stereo[m]",
            "-map",
            "[m]",
            music,
        ]
    )

    # 6) montaz: animowane premium tlo (granat/bordo/pomarancz) + wypalone napisy
    #    + cichy podklad + loudnorm -16 LUFS na finalnym miksie
    sub = (
        os.path.abspath(srt)
        .replace("\\", "\\\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
    )
    style = (
        "FontName=DejaVu Sans,Fontsize=19,Bold=1,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H64000000,"
        "BorderStyle=1,Outline=1,Shadow=1,Alignment=10,MarginL=90,MarginR=90"
    )
    bg = (
        f"gradients=s=1080x1920:c0=0x120a24:c1=0x4a0f1c:c2=0x161030:"
        f"c3=0x5a1e0a:nb_colors=4:type=radial:speed=0.006:d={total:.3f}:r=30,"
        "vignette=PI/4.5,eq=brightness=0.02*sin(2*PI*t/7):saturation=1.15:eval=frame,"
        "setsar=1,format=yuv420p[bgv];"
        f"[bgv]subtitles='{sub}':force_style='{style}'[v]"
    )
    filt = (
        bg + ";"
        "[0:a]volume=1.0[vo];[1:a]volume=0.06[mu];"
        "[vo][mu]amix=inputs=2:duration=first:dropout_transition=0,"
        "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]"
    )
    out_mp4 = os.path.join(OUT, "sample_tomstyl_11.mp4")
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            voice_wav,
            "-i",
            music,
            "-filter_complex",
            filt,
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
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-t",
            f"{total:.3f}",
            out_mp4,
        ]
    )
    print(f"DONE={out_mp4}")


if __name__ == "__main__":
    main()
