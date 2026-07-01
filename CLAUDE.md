# CLAUDE.md

This repo turns a **theme into a finished 9:16 animation** via frontier video models routed through fal or OpenRouter.

**Read [`AGENTS.md`](AGENTS.md) — it's the playbook** for how to take the user's theme and produce a
finished clip in `out/` (commands, model choice, the generate→inspect→iterate loop, and the gotchas).

Quick orientation:
- `pipeline/falkit.py` — provider model calls (image / text-to-video / image-to-video / lip-sync).
- `pipeline/make.py` — one-command driver (`animate` / `i2v` / `still` / `sing`).
- `pipeline/finish.py` — 9:16 grade + film finish + title/logo/CTA/captions.
- Cost is not a concern; always use the best model for the job.
