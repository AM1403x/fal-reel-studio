"""finish.py — turn a generated clip into a publish-ready 9:16 reel.

Conforms to 1080x1920 H.264, optional colour grade + a film/handheld "de-AI" finish,
optional top-left logo, on-screen title, burned captions, and an end-card CTA.
Keeps the clip's own audio unless --audio supplies a track to overlay.

Usage:
  python3 pipeline/finish.py --in raw.mp4 --out reel.mp4 \
      [--title "Free the Entangle"] [--logo logo.png] [--cta "Out now"] \
      [--ass captions.ass] [--audio song.wav] [--no-film]
"""
import argparse, os
from ffx import FF, check

FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
GRADE = "eq=brightness=0.02:saturation=1.07:contrast=1.04"
# gentle handheld drift + film grain + vignette — softens the synthetic look
FILMIFY = ("crop=iw*0.965:ih*0.965:'(iw-ow)/2+5*sin(2*PI*t/3)':'(ih-oh)/2+4*cos(2*PI*t/2.6)',"
           "scale=1080:1920,vignette=PI/6,noise=alls=3:allf=t,eq=contrast=1.02")


def _font(name):
    p = os.path.join(FONTS, name)
    return p if os.path.exists(p) else name  # fall back to fontconfig name


def finish(src, out, grade=None, film=True, title=None, logo=None, cta=None, ass=None, audio=None):
    g = grade or GRADE
    fonts_dir = f":fontsdir={FONTS}" if os.path.isdir(FONTS) else ""
    chain = [f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,{g}"]
    if film:
        chain.append(FILMIFY)
    vlabel = "[vbase]"
    filt = ",".join(chain) + vlabel

    inputs = ["-i", src]
    over_idx = 1
    if audio:
        inputs += ["-i", audio]; aud_idx = over_idx; over_idx += 1
    last = "vbase"
    if logo:
        inputs += ["-loop", "1", "-i", logo]
        filt += f";[{over_idx}:v]scale=240:-1[lg];[{last}][lg]overlay=34:96[vlogo]"
        last = "vlogo"; over_idx += 1
    if ass:
        filt += f";[{last}]ass={ass}{fonts_dir}[vass]"; last = "vass"
    if title:
        filt += (f";[{last}]drawtext=fontfile='{_font('Arial Bold.ttf')}':text='{title}':fontsize=46:"
                 f"fontcolor=white:shadowcolor=black@0.6:shadowx=2:shadowy=2:x=55:y=170[vtitle]")
        last = "vtitle"
    if cta:
        filt += (f";[{last}]drawtext=fontfile='{_font('Arial.ttf')}':text='{cta}':fontsize=52:fontcolor=white:"
                 f"borderw=3:bordercolor=black@0.85:x=(w-tw)/2:y=h*0.8:enable='gte(t\\,2.5)'[vcta]")
        last = "vcta"
    filt += f";[{last}]format=yuv420p[v]"

    cmd = [FF, "-y", *inputs, "-filter_complex", filt, "-map", "[v]"]
    if audio:
        cmd += ["-map", f"{aud_idx}:a", "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-shortest"]
    else:
        cmd += ["-map", "0:a?"]
    cmd += ["-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-maxrate", "14M", "-bufsize", "20M", "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-level", "4.2", "-g", "60", "-color_range", "tv",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    check(cmd)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--grade"); ap.add_argument("--no-film", action="store_true")
    ap.add_argument("--title"); ap.add_argument("--logo"); ap.add_argument("--cta")
    ap.add_argument("--ass"); ap.add_argument("--audio")
    a = ap.parse_args()
    finish(a.src, a.out, a.grade, not a.no_film, a.title, a.logo, a.cta, a.ass, a.audio)
    print("finished ->", a.out)
