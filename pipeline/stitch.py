"""stitch.py — join multiple clips into one seamless reel with transitions.

Crossfades consecutive clips (xfade) so multi-theme videos flow as one. Conforms everything to
1080x1920 / 30fps first. Audio: pass --audio to lay one soundtrack across the whole reel
(the usual case for a multi-theme cut); otherwise the result is silent (add audio in finish.py).

Usage:
  python3 pipeline/stitch.py --clips out/a.mp4 out/b.mp4 out/c.mp4 --out out/joined.mp4 \
      [--transition fade] [--xdur 0.6] [--audio song.wav]

Typical multi-theme flow (the agent does this):
  make.py animate --theme A --raw --out out/a.mp4
  make.py animate --theme B --raw --out out/b.mp4
  stitch.py --clips out/a.mp4 out/b.mp4 --out out/joined.mp4
  finish.py --in out/joined.mp4 --out out/final.mp4 --title "..." --audio song.wav
"""
import argparse, os
from ffx import FF, check, probe_duration

# common seamless transitions (any ffmpeg xfade name works)
TRANSITIONS = ["fade", "fadeblack", "dissolve", "smoothleft", "smoothright",
               "slideup", "slidedown", "circleopen", "radial", "wipeleft"]


def stitch(clips, out, transition="fade", xdur=0.6, audio=None):
    if len(clips) == 1:
        check([FF, "-y", "-i", clips[0], "-c", "copy", out])
        return out
    inputs, filt = [], []
    for c in clips:
        inputs += ["-i", c]
    # normalize each stream to a common canvas so xfade has matching geometry
    for i in range(len(clips)):
        filt.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                    f"crop=1080:1920,setsar=1,fps=30,format=yuv420p[v{i}]")
    prev, cum = "v0", probe_duration(clips[0])
    for i in range(1, len(clips)):
        off = max(0.1, cum - xdur)
        filt.append(f"[{prev}][v{i}]xfade=transition={transition}:duration={xdur}:offset={off:.3f}[x{i}]")
        prev, cum = f"x{i}", cum + probe_duration(clips[i]) - xdur
    cmd = [FF, "-y", *inputs]
    if audio:
        cmd += ["-i", audio]
    cmd += ["-filter_complex", ";".join(filt), "-map", f"[{prev}]"]
    if audio:
        cmd += ["-map", f"{len(clips)}:a", "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-shortest",
                "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-an"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
            "-profile:v", "high", "-level", "4.2", "-color_range", "tv", "-movflags", "+faststart", out]
    check(cmd)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", nargs="+", required=True, help="clips in order")
    ap.add_argument("--out", required=True)
    ap.add_argument("--transition", default="fade", help=f"one of: {', '.join(TRANSITIONS)}")
    ap.add_argument("--xdur", type=float, default=0.6, help="transition seconds")
    ap.add_argument("--audio", help="optional soundtrack across the whole reel")
    a = ap.parse_args()
    stitch(a.clips, a.out, a.transition, a.xdur, a.audio)
    print("stitched ->", a.out)
