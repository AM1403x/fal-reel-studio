# DECISIONS.md

Running log of every hardcoded constant, threshold, limit, and assumption baked into the codebase.

| Date | Area | Decision | Value / Details | Rationale | Review trigger |
|------|------|----------|-----------------|-----------|----------------|
| 2026-06-30 | openrouter-polling | Poll async OpenRouter video jobs every 30 seconds for up to 120 polls | 30s interval, 120 polls | OpenRouter video generation is async and can take minutes; this avoids tight polling while allowing up to one hour for long jobs | OpenRouter publishes different polling guidance or jobs regularly exceed one hour |
| 2026-06-30 | openrouter-kling-resolution | Downgrade OpenRouter Kling requests from 1080p to 720p | `kwaivgi/kling-v3.0-pro` with `resolution=1080p` becomes `720p` | OpenRouter currently lists Kling 3.0 Pro support at 720p, while this repo defaults to 1080p for other providers | OpenRouter adds 1080p support for Kling 3.0 Pro |
| 2026-06-30 | openrouter-seedance-aspect | Generate `2:3` Seedance requests as `3:4`, then finish locally at `2:3` | OpenRouter Seedance supports `3:4` but not exact `2:3` | Preserves user-requested portrait output ratio while using the closest available generation shape | OpenRouter adds exact `2:3` video support |
