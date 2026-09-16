#!/usr/bin/env python3
"""Montaz z tlem wideo (Ken Burns) na zdjeciach z folderu demos/assets/.

Wejscie: gotowy lektor out/voice_11.wav + napisy out/captions_11.srt
(produkuje je build_demo_elevenlabs.py). Zdjecia tla: demos/assets/*.jpg
(dowolne, na wolnej licencji, np. Wikimedia Commons CC BY-SA - patrz ATTRIBUTION).

Cechy:
- gladki, WYSRODKOWANY zoom (bez trzesienia typowego dla zoompan z panorama),
- crossfade miedzy kadrami,
- grading + winieta, wypalone napisy,
- audio: fade-in + stale wzmocnienie do ~-16 LUFS + limiter szczytow
  (bez pompowania dynamicznego loudnorm),
- opcjonalne przyspieszenie lektora: SPEED=1.07 python3 build_demo_broll.py

Uruchomienie:
  python3 demos/build_demo_broll.py
"""

import glob
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "demos", "assets")
OUT = os.path.join(ROOT, "out")

VOICE_IN = os.path.join(OUT, "voice_11.wav")
SRT_IN = os.path.join(OUT, "captions_11.srt")
VOICE = os.path.join(OUT, "voice_broll.wav")
MUSIC = os.path.join(OUT, "music_broll.wav")
SRT = os.path.join(OUT, "captions_broll.srt")
FINAL = os.path.join(OUT, "sample_broll.mp4")

SPEED = float(os.getenv("SPEED", "1.0"))
XF = 0.6
FPS = 30


def probe_dur(p):
    return float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                p,
            ]
        )
        .decode()
        .strip()
    )


def run(cmd, cap=True):
    return subprocess.run(cmd, check=True, capture_output=cap)


def scale_ts(ts, f):
    h, m, rest = ts.split(":")
    s, ms = rest.split(",")
    tot = int(round(((int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)) / f))
    ms = tot % 1000
    tot //= 1000
    return f"{tot // 3600:02d}:{tot % 3600 // 60:02d}:{tot % 60:02d},{ms:03d}"


def main():
    imgs = sorted(
        glob.glob(os.path.join(ASSETS, "*.jpg"))
        + glob.glob(os.path.join(ASSETS, "*.png"))
    )
    if not imgs:
        raise SystemExit("Brak zdjec w demos/assets/ (dodaj *.jpg na wolnej licencji).")

    # 1) lektor (opcjonalnie przyspieszony) + napisy przeliczone
    if SPEED > 1.001:
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                VOICE_IN,
                "-af",
                f"atempo={SPEED}",
                "-ar",
                "44100",
                VOICE,
            ]
        )
        src = open(SRT_IN, encoding="utf-8").read()
        import re

        out = re.sub(
            r"(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)",
            lambda m: (
                scale_ts(m.group(1), SPEED) + " --> " + scale_ts(m.group(2), SPEED)
            ),
            src,
        )
        open(SRT, "w", encoding="utf-8").write(out)
    else:
        run(["ffmpeg", "-y", "-i", VOICE_IN, "-c", "copy", VOICE])
        open(SRT, "w", encoding="utf-8").write(open(SRT_IN, encoding="utf-8").read())

    total = probe_dur(VOICE)
    n = len(imgs)
    D = (total + (n - 1) * XF) / n
    frames = int(round(D * FPS))

    # 2) muzyka pod dlugosc
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
            MUSIC,
        ]
    )

    # 3) klipy Ken Burns (gladki, wysrodkowany zoom + pre-scale 2x)
    clips = []
    for i, src in enumerate(imgs):
        clip = os.path.join(OUT, f"_kb_{i}.mp4")
        z = (
            "min(zoom+0.0008,1.35)"
            if i % 2 == 0
            else "if(lte(zoom,1.0),1.35,max(zoom-0.0008,1.0))"
        )
        vf = (
            "scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
            f"zoompan=z='{z}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s=1080x1920:fps={FPS},setsar=1,format=yuv420p"
        )
        run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                src,
                "-t",
                f"{D:.3f}",
                "-filter_complex",
                vf,
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(FPS),
                clip,
            ]
        )
        clips.append(clip)

    # 4) xfade + grading + napisy
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    fc, prev = [], "[0:v]"
    for k in range(1, n):
        off = k * (D - XF)
        fc.append(
            f"{prev}[{k}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{k}]"
        )
        prev = f"[x{k}]"
    sub = (
        os.path.abspath(SRT)
        .replace("\\", "\\\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
    )
    style = (
        "FontName=DejaVu Sans,Fontsize=19,Bold=1,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BackColour=&H64000000,BorderStyle=1,Outline=2,"
        "Shadow=1,Alignment=2,MarginV=150,MarginL=80,MarginR=80"
    )
    fc.append(
        f"{prev}eq=contrast=1.08:saturation=1.12:gamma=0.98,vignette=PI/4.2,"
        f"format=yuv420p[vg];[vg]subtitles='{sub}':force_style='{style}'[v]"
    )

    # audio bez dynamicznego loudnorm: fade-in, wzmocnienie stale, limiter
    pre = os.path.join(OUT, "_premix.wav")
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            VOICE,
            "-i",
            MUSIC,
            "-filter_complex",
            "[0:a]afade=t=in:st=0:d=0.12,volume=1.0[vo];[1:a]volume=0.06[mu];"
            "[vo][mu]amix=inputs=2:duration=first:normalize=0[mix]",
            "-map",
            "[mix]",
            "-ar",
            "48000",
            pre,
        ]
    )
    p = subprocess.run(
        [
            "ffmpeg",
            "-i",
            pre,
            "-af",
            "loudnorm=I=-16:print_format=json",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    ).stderr
    meas = json.loads(p[p.rindex("{") : p.rindex("}") + 1])
    gain = -16.0 - float(meas["input_i"])

    run(
        [
            "ffmpeg",
            "-y",
            *inputs,
            "-i",
            pre,
            "-filter_complex",
            ";".join(fc),
            "-af",
            f"volume={gain:.2f}dB,alimiter=limit=0.841:attack=5:release=50:asc=1",
            "-map",
            "[v]",
            "-map",
            f"{n}:a",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-profile:v",
            "high",
            "-r",
            str(FPS),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            FINAL,
        ],
        cap=False,
    )
    for c in clips:
        os.remove(c)
    os.remove(pre)
    print("FINAL:", FINAL, f"{probe_dur(FINAL):.2f}s")


if __name__ == "__main__":
    main()
