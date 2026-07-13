# fal-reel-studio

**Describe a theme → get a finished 9:16 animation.** Powered by the best AI video models
(Veo 3.1, Kling 3.0 Pro, Seedance 2.0) through [fal.ai](https://fal.ai) or [OpenRouter](https://openrouter.ai), and driven by
a frontier coding model (Claude Code / Cursor) — you talk, it builds. No coding required.

---

## The recommended way to use it (60 seconds)

1. **Get a provider key**. For fal, go to [fal.ai](https://fal.ai) → *API Keys*. For OpenRouter, go to [OpenRouter](https://openrouter.ai) → *Keys*. Copy `.env.example` to `.env` and paste one or both:
   ```
   FAL_KEY=your_key_here
   OPENROUTER_API_KEY=your_key_here
   ```
2. **Open this folder in [Claude Code](https://claude.com/claude-code)** (or Cursor).
3. **Just ask**, e.g.:
   > "I want an animation about *a paper boat drifting through a glowing night city, dreamy.*"

   It will **always ask you 3 quick things** (how long · one theme or several to stitch · aspect ratio), then **propose a short plan** — which single best model it'll use *and why* — and wait for your **go-ahead before rendering**. On approval it builds the finished clip into `out/`. Ask for changes in plain English and it iterates.

> **Recommended tool:** Claude Code + this repo + a provider key. That combination *is* the "go-to tool" — a frontier model doing the prompting/iterating, the best video models doing the rendering.

---

## What it makes

- **Theme → animation** (text-to-video) — the main flow
- **Multiple themes → one seamless video** — generated separately, then stitched with transitions
- **Still → animation** (image-to-video) — for tighter art direction
- **Singing character** — a face lip-synced to a song (optional; most themes are pure animation)
- **Auto-finish** — cinematic grade + subtle film/handheld grain (kills the "AI sheen"), optional title, logo, CTA, captions → on-spec 1080×1920 MP4

## The models (best available; cost is not optimized)

| Job | Models |
|---|---|
| Theme → video | **Veo 3.1** (default) · Kling 3.0 Pro · Seedance 2.0 |
| Still → animation | **Kling 3.0 Pro** (default) · Veo 3.1 · Seedance 2.0 |
| Stills | **FLUX Pro 1.1 Ultra** · Nano Banana (consistent characters) |
| Lip-sync | sync.so lipsync-2-pro |

Provider notes:
- fal remains the default route.
- OpenRouter is opt-in with `--provider openrouter` and supports the main video flow: Veo 3.1, Kling 3.0 Pro, Seedance 2.0, plus image-to-video.
- Singing still uses fal because the repo's vocal isolation and lip-sync models are not exposed by OpenRouter.

## Manual use (optional — the agent does this for you)

```sh
pip install -r requirements.txt
python3 pipeline/make.py animate --theme "neon koi swimming through ink, slow, cinematic" --duration 8 --out out/koi.mp4
python3 pipeline/make.py animate --provider openrouter --theme "neon koi swimming through ink, slow, cinematic" --duration 8 --out out/koi.mp4
```
More commands + example themes in [`examples/themes.md`](examples/themes.md).

## Notes

- Frontier model IDs move fast. If a call 404s, update `MODELS` in [`pipeline/falkit.py`](pipeline/falkit.py) from [fal.ai/models](https://fal.ai/models) — the agent can do this.
- For OpenRouter model IDs, update `OPENROUTER_MODELS` in [`pipeline/falkit.py`](pipeline/falkit.py) from [OpenRouter video models](https://openrouter.ai/docs/guides/overview/multimodal/video-generation).
- `pip install` brings a bundled ffmpeg (with libass for captions). On macOS run `bash pipeline/link_fonts.sh` once if you want the title/caption fonts.
- Each render hits the selected provider and costs credits. One good hero clip → many posts (reuse the footage).
