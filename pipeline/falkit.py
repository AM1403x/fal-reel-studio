"""falkit — frontier image / video / lip-sync generation through one fal.ai key.

Cost is not optimized for here: the defaults are the BEST models available (mid-2026).
If a call 404s, the model id moved — check https://fal.ai/models and update MODELS below.

All generators return a local file path. Set FAL_KEY in the environment or a .env file.
"""
import os, sys, urllib.request

# ---- Frontier model registry (mid-2026). Swap freely; these are the current best. ----
MODELS = {
    # Text -> video (a theme/prompt straight to an animated clip)
    "veo3":         "fal-ai/veo3.1",                            # Google Veo 3.1 - overall quality leader, up to 4K, native audio
    "kling":        "fal-ai/kling-video/v3/pro/text-to-video",  # Kling 3.0 Pro - best motion + human performance
    "seedance":     "bytedance/seedance-2.0/text-to-video",     # Seedance 2.0 - cinematic, multi-shot, director camera
    # Image -> video (bring a still to life)
    "veo3_i2v":     "fal-ai/veo3.1/image-to-video",
    "kling_i2v":    "fal-ai/kling-video/v3/pro/image-to-video",
    "seedance_i2v": "bytedance/seedance-2.0/image-to-video",
    # Stills (frontier image)
    "flux":         "fal-ai/flux-pro/v1.1-ultra",               # FLUX Pro 1.1 Ultra - top photoreal text-to-image
    "nano_edit":    "fal-ai/nano-banana/edit",                  # Nano Banana (Gemini) - reference-consistent edits / characters
    "nano":         "fal-ai/nano-banana",                       # Nano Banana - text-to-image, great instruction following
    # Character lip-sync + vocal isolation (only for singing-character themes)
    "lipsync":      "fal-ai/sync-lipsync/v2/pro",               # sync.so lipsync-2-pro
    "demucs":       "fal-ai/demucs",
}


def load_key():
    if os.environ.get("FAL_KEY"):
        return
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    envf = os.path.join(here, ".env")
    if os.path.exists(envf):
        for line in open(envf):
            if line.strip().startswith("FAL_KEY="):
                os.environ["FAL_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not os.environ.get("FAL_KEY"):
        sys.exit("FAL_KEY not set. Put FAL_KEY=... in a .env file (copy .env.example) or export it.")


def _fal():
    try:
        import fal_client
    except ImportError:
        sys.exit("fal-client missing -> pip install -r requirements.txt")
    return fal_client


def upload(path):
    return _fal().upload_file(path)


def _download(url, out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    urllib.request.urlretrieve(url, out)
    return out


def _media_url(r, keys=("video", "image", "images", "audio")):
    """Schema-tolerant extractor for the produced media URL across fal models."""
    if isinstance(r, dict):
        for k in keys:
            v = r.get(k)
            if isinstance(v, str) and v.startswith("http"):
                return v
            if isinstance(v, dict) and isinstance(v.get("url"), str):
                return v["url"]
            if isinstance(v, list) and v:
                hit = _media_url(v[0], keys)
                if hit:
                    return hit
        for v in r.values():
            hit = _media_url(v, keys)
            if hit:
                return hit
    elif isinstance(r, list):
        for v in r:
            hit = _media_url(v, keys)
            if hit:
                return hit
    return None


def _run(model_key, args, out):
    mid = MODELS.get(model_key, model_key)  # accept a raw fal id too
    r = _fal().subscribe(mid, arguments=args)
    url = _media_url(r)
    if not url:
        sys.exit(f"{mid}: no media url in response. Keys: {list(r) if isinstance(r, dict) else type(r)}")
    return _download(url, out)


# ---- Generators (minimal args + **extra passthrough so you can tune any model param) ----

def text_to_video(prompt, out, model="veo3", aspect="9:16", **extra):
    """Theme/prompt -> animated clip. model: veo3 | kling | seedance (or a raw fal id)."""
    load_key()
    args = {"prompt": prompt, "aspect_ratio": aspect}
    args.update(extra)  # e.g. resolution="1080p", duration="8", generate_audio=True
    return _run(model, args, out)


def image_to_video(image, out, prompt="", model="kling_i2v", aspect="9:16", **extra):
    """Still -> animation. model: kling_i2v | veo3_i2v | seedance_i2v."""
    load_key()
    args = {"image_url": upload(image), "prompt": prompt, "aspect_ratio": aspect}
    args.update(extra)
    return _run(model, args, out)


def image(prompt, out, model="flux", aspect="9:16", refs=None, **extra):
    """Frontier still. refs=[paths] routes to Nano Banana edit (reference-consistent characters/scenes)."""
    load_key()
    if refs:
        args = {"prompt": prompt, "image_urls": [upload(p) for p in refs], "aspect_ratio": aspect}
        args.update(extra)
        return _run("nano_edit", args, out)
    args = {"prompt": prompt, "aspect_ratio": aspect}
    args.update(extra)
    return _run(model, args, out)


def lipsync(video, audio, out, sync_mode="cut_off"):
    """Re-drive a face's mouth to an audio track (sync.so lipsync-2-pro). Use the isolated vocal for singing."""
    load_key()
    args = {"video_url": upload(video), "audio_url": upload(audio), "sync_mode": sync_mode}
    return _run("lipsync", args, out)


def isolate_vocal(audio, out):
    """Demucs vocal stem (drive lip-sync on this, not the full mix)."""
    load_key()
    r = _fal().subscribe(MODELS["demucs"], arguments={"audio_url": upload(audio)})
    url = _media_url(r, keys=("vocals", "vocal", "audio"))
    if not url:
        sys.exit(f"demucs: no vocals stem in response: {list(r) if isinstance(r, dict) else type(r)}")
    return _download(url, out)
