#!/usr/bin/env bash
# Recreate the local font symlinks compose.py expects (macOS). Run once after clone.
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)/assets/fonts"
mkdir -p "$DIR"
for f in \
  "/System/Library/Fonts/Supplemental/Impact.ttf" \
  "/System/Library/Fonts/Supplemental/Arial.ttf" \
  "/System/Library/Fonts/Supplemental/Arial Bold.ttf" \
  "/System/Library/Fonts/Supplemental/Arial Black.ttf" \
  "/System/Library/Fonts/Supplemental/Futura.ttc" \
  "/System/Library/Fonts/HelveticaNeue.ttc" \
  "/System/Library/Fonts/Avenir Next.ttc" \
  "/System/Library/Fonts/Avenir.ttc"; do
  [ -e "$f" ] && ln -sf "$f" "$DIR/" && echo "linked $(basename "$f")"
done
