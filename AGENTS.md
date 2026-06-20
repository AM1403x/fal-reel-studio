# AGENTS.md — how to make an animation in this repo

You are a coding agent (Claude Code / Cursor) with this repo open. The user describes a theme for a
short vertical video; you produce a **finished 9:16 reel in `out/`** using the fal pipeline.
**Cost is not a concern — always reach for the best model.**

## Setup (once)
- Ensure `FAL_KEY` is set: check `.env`. If missing, ask the user to paste their key from fal.ai into `.env`.
- `pip install -r requirements.txt` (brings fal-client, Pillow, and a libass-enabled ffmpeg).
- macOS + want title/caption fonts: `bash pipeline/link_fonts.sh`.

## The loop
1. **Clarify lightly** (don't over-ask — good defaults exist): duration (default 8s), vibe/style, audio yes/no, any title/logo/CTA to overlay.
2. **Write a strong prompt.** Be specific: subject, camera move, lighting, lens/film stock, motion, mood. Vague → generic.
3. **Generate** (commands below).
4. **Inspect.** Extract a few frames with ffmpeg and actually look at them — check artifacts (hands, faces, warping), framing, and motion. Don't ship blind.
5. **Iterate.** Refine the prompt or switch `--model` and regenerate until it's good.
6. Finishing (grade + film grain) is automatic. Add `--title/--logo/--cta/--ass` per the user's wishes.
7. Report the `out/` path and show a representative frame.

## Commands
```sh
# theme -> animation (text-to-video; Veo 3.1 default)
python3 pipeline/make.py animate --theme "<prompt>" --duration 8 --out out/<name>.mp4 [--model kling|seedance] [--audio-native]

# more control: still first, then bring it to life
python3 pipeline/make.py still --prompt "<prompt>" --out out/still.png
python3 pipeline/make.py i2v --image out/still.png --motion "<camera + motion>" --out out/<name>.mp4 [--model kling_i2v|veo3_i2v|seedance_i2v]

# singing character (still + song -> lip-synced)
python3 pipeline/make.py sing --image singer.png --song song.mp3 --out out/sing.mp4
```
Finishing flags on any of the above: `--title "..." --logo logo.png --cta "Out now" --ass captions.ass --audio track.wav --no-film`.

## Picking the best model per job
- **Veo 3.1** (`veo3`): overall quality, prompt adherence, up to 4K, native audio. Default for theme→video.
- **Kling 3.0 Pro** (`kling` / `kling_i2v`): best motion + human/character performance. Default for still→animation and anything with people/dancing.
- **Seedance 2.0** (`seedance`): cinematic multi-shot, director-level camera, strong lip-sync.
- **Stills**: FLUX Pro Ultra (`flux`); for a **recurring character** across clips, use Nano Banana with `--refs` so the face stays consistent.

## Hard-won tips (read before you render)
- Faces and **hands** are where AI breaks — keep hands simple/still or out of frame; frame faces large.
- **Big faces lip-sync well; crowds do not.** A "choir/group sing" won't sync per-face — do a tight 1–2 person shot, or cut between solo shots.
- Generate **2–4 candidates** and pick the best. One strong hero → many posts (reuse footage).
- If a model param errors, check that model's current input schema on fal.ai and pass extra params through (`make.py` forwards `--resolution/--duration`; `falkit` functions accept arbitrary `**extra`).
- Tune `MODELS` in `pipeline/falkit.py` whenever a newer frontier model ships.
