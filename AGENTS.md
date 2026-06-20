# AGENTS.md — how to make an animation in this repo

You are a coding agent (Claude Code / Cursor) with this repo open. The user describes a theme for a
short vertical video; you produce a **finished 9:16 reel in `out/`** using the fal pipeline.
**Cost is not a concern — always reach for the best model.**

## Setup (once)
- Ensure `FAL_KEY` is set: check `.env`. If missing, ask the user to paste their key from fal.ai into `.env`.
- `pip install -r requirements.txt` (brings fal-client, Pillow, and a libass-enabled ffmpeg).
- macOS + want title/caption fonts: `bash pipeline/link_fonts.sh`.

## The loop (follow this every time)

**1. ALWAYS ask these 3 questions first — every single request, no exceptions.** Confirm all three before planning, even if the user already hinted at some:
   1. **Duration** — how long? (single clips look best at 4–8s; or a longer cut?)
   2. **Theme(s)** — what's the idea, and **is this ONE theme, or MULTIPLE themes to stitch into one video?**
   3. **Format** — aspect ratio: 9:16 reel (default), 16:9, or square?

**2. Pick the SINGLE best model for THIS job.** Do **not** render across multiple models. Choose one based on the look (see "Model choice" below).

**3. Propose a short plan and WAIT FOR APPROVAL before the final render.** The plan must state:
   - the **chosen model and *why*** it's the best fit for this specific job
   - the theme/shot breakdown (one strong prompt per theme), durations, format
   - if multiple themes: the **transition style** and that they'll be stitched seamlessly
   - finishing (grade/film, any title/logo/CTA)
   Do not spend on the final render until the user approves.

**4. On approval, generate.**
   - Single theme → one clip → finish.
   - Multiple themes → generate each with `--raw`, then `stitch.py` (seamless transitions), then `finish.py` **once** over the joined cut (uniform grade + one title/CTA).

**5. Inspect** — extract frames, check artifacts (hands, faces, warping), framing, motion. Re-roll the *same* model / tweak the prompt if needed (don't fan out across models — you already picked and got the best one approved).

**6. Deliver** the `out/` path + a representative frame.

## Commands
```sh
# theme -> animation (text-to-video; Veo 3.1 default)
python3 pipeline/make.py animate --theme "<prompt>" --duration 8 --out out/<name>.mp4 [--model kling|seedance] [--audio-native]

# more control: still first, then bring it to life
python3 pipeline/make.py still --prompt "<prompt>" --out out/still.png
python3 pipeline/make.py i2v --image out/still.png --motion "<camera + motion>" --out out/<name>.mp4 [--model kling_i2v|veo3_i2v|seedance_i2v]

# OPTIONAL — singing character (still + song -> lip-synced). Most themes are pure animation; only use this when a face must mouth the words.
python3 pipeline/make.py sing --image singer.png --song song.mp3 --out out/sing.mp4
```
Finishing flags on any of the above: `--title "..." --logo logo.png --cta "Out now" --ass captions.ass --audio track.wav --no-film`.

```sh
# MULTIPLE themes -> one seamless stitched reel (generate raw, stitch with transitions, finish once)
python3 pipeline/make.py animate --theme "<theme A>" --raw --out out/a.mp4
python3 pipeline/make.py animate --theme "<theme B>" --raw --out out/b.mp4
python3 pipeline/stitch.py --clips out/a.mp4 out/b.mp4 --transition fade --xdur 0.6 --out out/joined.mp4
python3 pipeline/finish.py --in out/joined.mp4 --out out/final.mp4 --title "..." --audio song.wav
```
(`--raw` skips per-clip finishing so the join is clean and the grade/title are applied once over the whole cut. Transitions: `fade`, `dissolve`, `smoothleft`, `slideup`, `circleopen`, … — pick what suits the mood.)

## Picking the best model per job
- **Veo 3.1** (`veo3`): overall quality, prompt adherence, up to 4K, native audio. Default for theme→video.
- **Kling 3.0 Pro** (`kling` / `kling_i2v`): best motion + human/character performance. Default for still→animation and anything with people/dancing.
- **Seedance 2.0** (`seedance`): cinematic multi-shot, director-level camera, strong lip-sync.
- **Stills**: FLUX Pro Ultra (`flux`); for a **recurring character** across clips, use Nano Banana with `--refs` so the face stays consistent.

## Hard-won tips (read before you render)
- Faces and **hands** are where AI breaks — keep hands simple/still or out of frame; frame faces large.
- **Big faces lip-sync well; crowds do not.** A "choir/group sing" won't sync per-face — do a tight 1–2 person shot, or cut between solo shots.
- You already picked the single best model and got it approved — **don't fan out across models.** Render that model; if it misses, refine the prompt or re-roll the *same* model. One strong hero → many posts (reuse footage).
- If a model param errors, check that model's current input schema on fal.ai and pass extra params through (`make.py` forwards `--resolution/--duration`; `falkit` functions accept arbitrary `**extra`).
- Tune `MODELS` in `pipeline/falkit.py` whenever a newer frontier model ships.
