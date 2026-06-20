"""make.py — one-command animation reels via frontier fal models + the finishing pass.

  # theme -> animated 9:16 clip (best model, Veo 3.1 by default)
  python3 pipeline/make.py animate --theme "a paper boat drifting through a glowing night city, dreamy" \
      --duration 8 --out out/city.mp4 --title "Free the Entangle"

  # bring a still to life (best motion, Kling 3.0 Pro by default)
  python3 pipeline/make.py i2v --image still.png --motion "slow push-in, embers rising" --out out/shot.mp4

  # just a frontier still (FLUX Pro Ultra)
  python3 pipeline/make.py still --prompt "neon koi pond, top-down, cinematic" --out out/still.png

  # singing character: still + song -> lip-synced reel (uses the isolated vocal)
  python3 pipeline/make.py sing --image singer.png --song song.mp3 --out out/sing.mp4

--model overrides the default; --no-film disables the grain/handheld finish; finishing flags
(--title/--logo/--cta/--ass/--audio) pass straight through to finish.py.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import falkit
from finish import finish

OUT = "out"


def _tmp(name):
    os.makedirs(OUT, exist_ok=True)
    return os.path.join(OUT, name)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("animate", help="theme -> animated clip (text-to-video)")
    a.add_argument("--theme", required=True); a.add_argument("--model", default="veo3")
    a.add_argument("--duration", default="8"); a.add_argument("--resolution", default="1080p")
    a.add_argument("--audio-native", action="store_true", help="let the model generate native audio")

    i = sub.add_parser("i2v", help="still -> animation (image-to-video)")
    i.add_argument("--image", required=True); i.add_argument("--motion", default="")
    i.add_argument("--model", default="kling_i2v"); i.add_argument("--duration", default="8")
    i.add_argument("--resolution", default="1080p")

    s = sub.add_parser("still", help="frontier still (text-to-image)")
    s.add_argument("--prompt", required=True); s.add_argument("--model", default="flux")
    s.add_argument("--refs", nargs="*", help="reference images -> Nano Banana edit (consistent character)")

    g = sub.add_parser("sing", help="singing character: still + song -> lip-synced reel")
    g.add_argument("--image", required=True); g.add_argument("--song", required=True)

    # shared finishing flags
    for p in (a, i, g):
        p.add_argument("--out", required=True)
        p.add_argument("--raw", action="store_true", help="skip finish; output the raw gen (for stitching, then finish once)")
        p.add_argument("--no-film", action="store_true")
        p.add_argument("--title"); p.add_argument("--logo"); p.add_argument("--cta")
        p.add_argument("--ass"); p.add_argument("--audio")
    s.add_argument("--out", required=True)

    args = ap.parse_args()

    if args.cmd == "still":
        falkit.image(args.prompt, args.out, model=args.model, refs=args.refs)
        print("still ->", args.out); return

    if args.cmd == "animate":
        raw = _tmp("_raw_animate.mp4")
        falkit.text_to_video(args.theme, raw, model=args.model,
                             resolution=args.resolution, duration=args.duration,
                             generate_audio=bool(args.audio_native))

    elif args.cmd == "i2v":
        raw = _tmp("_raw_i2v.mp4")
        falkit.image_to_video(args.image, raw, prompt=args.motion, model=args.model,
                              resolution=args.resolution, duration=args.duration)

    elif args.cmd == "sing":
        raw = _tmp("_raw_sing.mp4")
        vocal = _tmp("_vocal.wav")
        falkit.isolate_vocal(args.song, vocal)                 # drive sync on the isolated vocal
        anim = _tmp("_sing_anim.mp4")
        falkit.image_to_video(args.image, anim, prompt="the person sings to camera, natural motion",
                              model="kling_i2v", duration="8")
        falkit.lipsync(anim, vocal, raw)                       # sync.so lipsync-2-pro
        if not args.audio:
            args.audio = args.song                             # final clip carries the real song

    if getattr(args, "raw", False):
        os.replace(raw, args.out)
        print("raw ->", args.out, "(stitch, then finish)")
        return
    finish(raw, args.out, film=not args.no_film, title=args.title, logo=args.logo,
           cta=args.cta, ass=args.ass, audio=args.audio)
    print("reel ->", args.out)


if __name__ == "__main__":
    main()
