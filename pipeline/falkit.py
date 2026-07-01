"""falkit — frontier image / video / lip-sync generation through provider APIs.

Cost is not optimized for here: the defaults are the BEST models available (mid-2026).
If a call 404s, the model id moved — check the provider's model list and update below.

All generators return a local file path. Set FAL_KEY or OPENROUTER_API_KEY in the environment
or a .env file.
"""
import base64, json, mimetypes, os, sys, time, urllib.error, urllib.request

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

OPENROUTER_MODELS = {
    # Text/image -> video through OpenRouter's async video API
    "veo3":         "google/veo-3.1",
    "kling":        "kwaivgi/kling-v3.0-pro",
    "seedance":     "bytedance/seedance-2.0",
    "veo3_i2v":     "google/veo-3.1",
    "kling_i2v":    "kwaivgi/kling-v3.0-pro",
    "seedance_i2v": "bytedance/seedance-2.0",
    # Stills through OpenRouter's image API
    "flux":         "black-forest-labs/flux.2-pro",
    "nano_edit":    "google/gemini-2.5-flash-image",
    "nano":         "google/gemini-2.5-flash-image",
}

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_POLL_SECONDS = 30  # See DECISIONS.md — openrouter-polling
OPENROUTER_MAX_POLLS = 120    # See DECISIONS.md — openrouter-polling


def _read_env(keys):
    for key in keys:
        if os.environ.get(key):
            return os.environ[key]
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    envf = os.path.join(here, ".env")
    if os.path.exists(envf):
        for line in open(envf):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            if k in keys and not os.environ.get(k):
                os.environ[k] = v.strip().strip('"').strip("'")
    for key in keys:
        if os.environ.get(key):
            return os.environ[key]
    return None


def load_key(provider="fal"):
    if provider == "openrouter":
        if not _read_env(("OPENROUTER_API_KEY", "OPENROUTER_KEY")):
            sys.exit("OPENROUTER_API_KEY not set. Put OPENROUTER_API_KEY=... in .env or export it.")
        return
    if not _read_env(("FAL_KEY",)):
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


def _write_bytes(data, out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "wb") as f:
        f.write(data)
    return out


def _media_url(r, keys=("video", "image", "images", "audio")):
    """Schema-tolerant extractor for the produced media URL across fal models."""
    if isinstance(r, dict):
        if isinstance(r.get("url"), str) and r["url"].startswith("http"):
            return r["url"]
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


def _normalize(model_key, args):
    """Smooth over per-model arg quirks so the common flags 'just work'."""
    mid = MODELS.get(model_key, model_key)
    if "veo" in mid and "duration" in args:          # Veo wants '4s' | '6s' | '8s'
        args["duration"] = f"{str(args['duration']).rstrip('s')}s"
    return args


def _run(model_key, args, out):
    mid = MODELS.get(model_key, model_key)  # accept a raw fal id too
    r = _fal().subscribe(mid, arguments=_normalize(model_key, args))
    url = _media_url(r)
    if not url:
        sys.exit(f"{mid}: no media url in response. Keys: {list(r) if isinstance(r, dict) else type(r)}")
    return _download(url, out)


def _openrouter_model(model_key):
    return OPENROUTER_MODELS.get(model_key, model_key)


def _openrouter_headers():
    return {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY'] if os.environ.get('OPENROUTER_API_KEY') else os.environ['OPENROUTER_KEY']}",
        "Content-Type": "application/json",
    }


def _openrouter_json(url, payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=_openrouter_headers())
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        sys.exit(f"OpenRouter HTTP {exc.code}: {detail}")


def _openrouter_download(url, out):
    req = urllib.request.Request(url, headers=_openrouter_headers())
    try:
        with urllib.request.urlopen(req) as response:
            return _write_bytes(response.read(), out)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        sys.exit(f"OpenRouter download HTTP {exc.code}: {detail}")


def _data_url(path):
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _openrouter_video(model_key, args, out):
    model = _openrouter_model(model_key)
    if model == "bytedance/seedance-2.0" and args.get("aspect_ratio") == "2:3":
        args["aspect_ratio"] = "3:4"
    if model == "kwaivgi/kling-v3.0-pro" and args.get("resolution") == "1080p":
        args["resolution"] = "720p"
    if "duration" in args:
        try:
            args["duration"] = int(str(args["duration"]).rstrip("s"))
        except ValueError:
            sys.exit(f"OpenRouter: duration must be a whole number of seconds, got {args['duration']!r}.")
    payload = {"model": model, **args}
    result = _openrouter_json(f"{OPENROUTER_BASE}/videos", payload)
    polling_url = result.get("polling_url")
    if not polling_url:
        sys.exit(f"OpenRouter: no polling_url in response: {result}")

    for _ in range(OPENROUTER_MAX_POLLS):
        status = _openrouter_json(polling_url)
        state = status.get("status")
        if state == "completed":
            urls = status.get("unsigned_urls") or []
            if not urls:
                sys.exit(f"OpenRouter: completed without video URL: {status}")
            return _openrouter_download(urls[0], out)
        if state in ("failed", "cancelled", "expired"):
            sys.exit(f"OpenRouter: generation {state}: {status.get('error', status)}")
        time.sleep(OPENROUTER_POLL_SECONDS)
    sys.exit("OpenRouter: generation timed out before completion.")


def _openrouter_image(model_key, args, out):
    model = _openrouter_model(model_key)
    if model.startswith("black-forest-labs/"):
        args.pop("aspect_ratio", None)
    payload = {"model": model, **args}
    result = _openrouter_json(f"{OPENROUTER_BASE}/images", payload)
    images = result.get("data") or []
    if not images or not images[0].get("b64_json"):
        sys.exit(f"OpenRouter: no image bytes in response: {result}")
    return _write_bytes(base64.b64decode(images[0]["b64_json"]), out)


# ---- Generators (minimal args + **extra passthrough so you can tune any model param) ----

def text_to_video(prompt, out, model="veo3", aspect="9:16", provider="fal", **extra):
    """Theme/prompt -> animated clip. model: veo3 | kling | seedance (or a raw fal id)."""
    load_key(provider)
    args = {"prompt": prompt, "aspect_ratio": aspect}
    args.update(extra)  # e.g. resolution="1080p", duration="8", generate_audio=True
    if provider == "openrouter":
        return _openrouter_video(model, args, out)
    return _run(model, args, out)


def image_to_video(image, out, prompt="", model="kling_i2v", aspect="9:16", provider="fal", **extra):
    """Still -> animation. model: kling_i2v | veo3_i2v | seedance_i2v."""
    load_key(provider)
    if provider == "openrouter":
        args = {
            "prompt": prompt,
            "aspect_ratio": aspect,
            "generate_audio": False,
            "frame_images": [{
                "type": "image_url",
                "image_url": {"url": _data_url(image)},
                "frame_type": "first_frame",
            }],
        }
        args.update(extra)
        return _openrouter_video(model, args, out)
    args = {"image_url": upload(image), "prompt": prompt, "aspect_ratio": aspect}
    args.update(extra)
    return _run(model, args, out)


def image(prompt, out, model="flux", aspect="9:16", refs=None, provider="fal", **extra):
    """Frontier still. refs=[paths] routes to Nano Banana edit (reference-consistent characters/scenes)."""
    load_key(provider)
    if provider == "openrouter":
        args = {"prompt": prompt, "aspect_ratio": aspect}
        if refs:
            args["input_references"] = [
                {"type": "image_url", "image_url": {"url": _data_url(p)}} for p in refs
            ]
            model = "nano_edit"
        args.update(extra)
        return _openrouter_image(model, args, out)
    if refs:
        args = {"prompt": prompt, "image_urls": [upload(p) for p in refs], "aspect_ratio": aspect}
        args.update(extra)
        return _run("nano_edit", args, out)
    args = {"prompt": prompt, "aspect_ratio": aspect}
    args.update(extra)
    return _run(model, args, out)


def lipsync(video, audio, out, sync_mode="cut_off", provider="fal"):
    """Re-drive a face's mouth to an audio track (sync.so lipsync-2-pro). Use the isolated vocal for singing."""
    if provider == "openrouter":
        sys.exit("OpenRouter does not provide the repo's lip-sync model. Use --provider fal for sing.")
    load_key(provider)
    args = {"video_url": upload(video), "audio_url": upload(audio), "sync_mode": sync_mode}
    return _run("lipsync", args, out)


def isolate_vocal(audio, out, provider="fal"):
    """Demucs vocal stem (drive lip-sync on this, not the full mix)."""
    if provider == "openrouter":
        sys.exit("OpenRouter does not provide the repo's vocal isolation model. Use --provider fal for sing.")
    load_key(provider)
    r = _fal().subscribe(MODELS["demucs"], arguments={"audio_url": upload(audio)})
    url = _media_url(r, keys=("vocals", "vocal", "audio"))
    if not url:
        sys.exit(f"demucs: no vocals stem in response: {list(r) if isinstance(r, dict) else type(r)}")
    return _download(url, out)
