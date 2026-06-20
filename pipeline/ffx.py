"""Shared ffmpeg helpers. This imageio ffmpeg build has NO ffprobe — probe via ffmpeg."""
import os, re, shutil, subprocess


def ffmpeg_bin():
    cand = os.path.expanduser("~/.local/bin/ffmpeg")
    return cand if os.path.exists(cand) else (shutil.which("ffmpeg") or "ffmpeg")


FF = ffmpeg_bin()


def run(cmd):
    """Run a command list, return CompletedProcess (text)."""
    return subprocess.run(cmd, capture_output=True, text=True)


def check(cmd):
    """Run and raise with tail of stderr on failure."""
    r = run(cmd)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed:\n" + (r.stderr or "")[-1200:])
    return r


def probe_duration(path):
    """Seconds, parsed from `ffmpeg -i` (no ffprobe available)."""
    r = run([FF, "-i", path])
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr or "")
    if not m:
        raise RuntimeError(f"could not probe duration of {path}\n{(r.stderr or '')[-600:]}")
    h, mn, s = m.groups()
    return int(h) * 3600 + int(mn) * 60 + float(s)
