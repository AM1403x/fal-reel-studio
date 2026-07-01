# Provider Routing

This repo keeps finishing local and swaps only the raw generation provider.

Flow:
```
User prompt
  -> pipeline/make.py chooses command + provider
  -> pipeline/falkit.py submits raw generation to fal or OpenRouter
  -> raw MP4 / still lands in out/
  -> stitch.py joins raw clips when needed
  -> finish.py applies one consistent grade, title, captions, logo, CTA, and audio
```

User-visible result:
- fal and OpenRouter produce the same final artifact shape: a local file in `out/`.
- fal remains the default provider.
- OpenRouter is selected with `--provider openrouter`.
- OpenRouter supports the main text-to-video and image-to-video flows for Veo 3.1, Kling 3.0 Pro, and Seedance 2.0.
- Singing-character generation remains fal-only because OpenRouter does not expose the repo's vocal isolation and lip-sync models.

OpenRouter seam:
- Text-to-video posts to `POST /api/v1/videos`, polls the returned `polling_url`, then downloads the first completed video URL.
- Image-to-video sends the local image as a first-frame data URL in `frame_images`; no external image hosting is required.
- OpenRouter image-to-video requests disable native audio because final audio is attached locally and provider-generated audio can fail safety checks.
- Still generation posts to `POST /api/v1/images` and writes the first returned base64 image.
- OpenRouter FLUX stills do not currently advertise aspect-ratio control, so the pipeline omits that parameter for FLUX and keeps aspect-ratio control for Nano Banana.
- OpenRouter Seedance does not currently expose exact `2:3` video generation, so `2:3` requests generate at `3:4` and finish locally at `2:3`.

Model aliases:
- `veo3` -> `google/veo-3.1`
- `kling` / `kling_i2v` -> `kwaivgi/kling-v3.0-pro`
- `seedance` / `seedance_i2v` -> `bytedance/seedance-2.0`
- `flux` -> `black-forest-labs/flux.2-pro`
- `nano` / `nano_edit` -> `google/gemini-2.5-flash-image`
