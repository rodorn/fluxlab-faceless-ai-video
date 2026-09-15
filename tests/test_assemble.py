"""Testy budowy komendy ffmpeg (bez uruchamiania ffmpeg)."""

from src.assemble import HEIGHT, WIDTH, build_ffmpeg_command


def _cmd(**kw):
    return build_ffmpeg_command(
        audio_path="out/voice.mp3",
        srt_path="out/captions.srt",
        out_path="out/video.mp4",
        duration=12.5,
        **kw,
    )


def test_command_starts_with_ffmpeg_overwrite():
    cmd = _cmd()
    assert cmd[0] == "ffmpeg"
    assert "-y" in cmd


def test_vertical_resolution_present():
    cmd = " ".join(_cmd())
    assert f"{WIDTH}x{HEIGHT}" in cmd
    assert WIDTH == 1080 and HEIGHT == 1920


def test_subtitles_burned_in():
    cmd = " ".join(_cmd())
    assert "subtitles=" in cmd
    assert "captions.srt" in cmd


def test_audio_and_music_mixed():
    cmd = " ".join(_cmd())
    assert "amix=inputs=2" in cmd
    assert "sine=frequency" in cmd  # placeholder muzyki w trybie demo


def test_output_and_maps():
    cmd = _cmd()
    assert cmd[-1] == "out/video.mp4"
    joined = " ".join(cmd)
    assert "-map [v]" in joined
    assert "-map [a]" in joined
    assert "libx264" in joined
    assert "yuv420p" in joined


def test_images_branch_uses_concat():
    cmd = " ".join(_cmd(images=["a.jpg", "b.jpg"]))
    assert "concat=n=2" in cmd
    assert "sine=frequency" not in cmd or "concat=n=2" in cmd  # koncat obecny
    assert cmd.count("-loop 1") == 2


def test_external_music_used_when_provided():
    cmd = " ".join(_cmd(music_path="assets/music.mp3"))
    assert "assets/music.mp3" in cmd
    assert "sine=frequency" not in cmd
