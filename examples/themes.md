# Example themes & commands

Copy a command, or just tell Claude Code the theme in plain English.

## Abstract / motion
```sh
python3 pipeline/make.py animate --theme "ink blooming into a galaxy in water, slow swirling, deep blues and gold, macro, cinematic" --duration 8 --out out/ink.mp4
python3 pipeline/make.py animate --theme "liquid chrome ribbons folding in zero gravity, soft studio light, hypnotic" --duration 8 --out out/chrome.mp4
```

## Nature / texture
```sh
python3 pipeline/make.py animate --theme "a single feather drifting up through a sunbeam in a misty forest, shot on 35mm, dreamy" --duration 8 --out out/feather.mp4
python3 pipeline/make.py animate --theme "golden wheat field rippling at sunrise, gentle wind, warm backlight, film grain" --duration 8 --out out/wheat.mp4
```

## Character / performance (Kling 3.0 Pro)
```sh
python3 pipeline/make.py still --prompt "a serene young woman, soft sunrise side-light, modest, photoreal portrait, 35mm" --out out/her.png
python3 pipeline/make.py i2v --image out/her.png --motion "she breathes and opens her eyes to the light, gentle handheld, slow push-in" --model kling_i2v --duration 8 --out out/her_motion.mp4
```

## Singing character (lip-synced to a song)
```sh
python3 pipeline/make.py sing --image out/her.png --song my_song.mp3 --out out/sing.mp4 --title "Song Title" --cta "Out now"
```

## With branding
Add to any `animate`/`i2v`/`sing` command: `--title "Free the Entangle" --logo logo.png --cta "Out now on Spotify"`.

## Tips
- Be specific (camera, light, lens, motion, mood). Vague prompts → generic clips.
- Try `--model kling` or `--model seedance` and compare; keep the best.
- Bigger faces sync/animate better than crowds.
