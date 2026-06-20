"""Stage 4 — build an animated ASS caption file for one clip window.

Reveals lyrics in short punchy chunks (<=4 words) synced to the vocal, with per-word karaoke
highlight (the highest-save-rate music caption style). Text stays inside IG safe zones.

Word timings come from a Whisper words JSON ({"segments":[{"words":[{word,start,end}]}]}).
Times are emitted CLIP-RELATIVE (the clip's audio starts at `start`).

Usage (test): python3 captions.py <words.json> <start> <end> <template> <out.ass>
"""
import sys, json

MAX_WORDS = 4  # punchy lines beat edge-to-edge segment dumps

# ASS colour = &HAABBGGRR. primary = sung/highlight, secondary = unsung (revealed white then fills).
TEMPLATES = {
    "hook_top":    dict(font="Avenir Next",    size=92,  primary="&H0007C1FF", secondary="&H00FFFFFF", oc="&H00000000", bold=-1, outline=5, shadow=1, align=8, marginv=150),
    "bold_bottom": dict(font="Impact",         size=120, primary="&H00FF66CC", secondary="&H00FFFFFF", oc="&H00000000", bold=0,  outline=6, shadow=2, align=2, marginv=380),
    "clean_lower": dict(font="Helvetica Neue", size=86,  primary="&H00C8FFC8", secondary="&H00FFFFFF", oc="&H00141414", bold=-1, outline=5, shadow=1, align=2, marginv=360),
}


def ass_time(t):
    cs = max(0, int(round(t * 100)))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _san(tok):
    return tok.replace("\\", "").replace("{", "(").replace("}", ")").strip()


def _kara(words, line_start):
    parts, prev = [], line_start
    for w in words:
        gap = int(round((w["start"] - prev) * 100))
        if gap > 0:
            parts.append(f"{{\\k{gap}}}")
        dur = max(1, int(round((w["end"] - w["start"]) * 100)))
        parts.append(f"{{\\k{dur}}}{_san(w['word'])} ")
        prev = w["end"]
    return "".join(parts).strip()


def _select(words_json, start, end):
    """In-window words, split into <=MAX_WORDS chunks (preserving order)."""
    data = json.load(open(words_json))
    chunks = []
    for seg in data.get("segments", []):
        ws = [w for w in seg.get("words", [])
              if "start" in w and "end" in w and w["end"] > start and w["start"] < end]
        for i in range(0, len(ws), MAX_WORDS):
            chunks.append(ws[i:i + MAX_WORDS])
    return chunks


def build(words_json, start, end, template, out_path):
    tpl = TEMPLATES[template]
    lines = _select(words_json, start, end)
    events = []
    for i, ws in enumerate(lines):
        ls = max(start, ws[0]["start"])
        le = min(end, ws[-1]["end"])
        nxt = lines[i + 1][0]["start"] if i + 1 < len(lines) else end
        disp_end = min(end, max(le, min(nxt, le + 0.35)))         # one chunk on screen at a time
        events.append((ls - start, disp_end - start, _kara(ws, ls)))

    style = (f"Style: Main,{tpl['font']},{tpl['size']},{tpl['primary']},{tpl['secondary']},"
             f"{tpl['oc']},&H64000000,{tpl['bold']},0,0,0,100,100,0,0,1,{tpl['outline']},{tpl['shadow']},"
             f"{tpl['align']},90,90,{tpl['marginv']},1")
    header = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n"
              "ScaledBorderAndShadow: yes\nWrapStyle: 2\n\n"
              "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
              "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, "
              "Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
              f"{style}\n\n[Events]\n"
              "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    body = "".join(
        f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Main,,0,0,0,,{{\\fad(120,100)}}{txt}\n"
        for s, e, txt in events
    )
    open(out_path, "w").write(header + body)
    return out_path, len(events)


if __name__ == "__main__":
    wj, s, e, tpl, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4], sys.argv[5]
    _, n = build(wj, s, e, tpl, out)
    print(f"{n} caption chunks -> {out}")
