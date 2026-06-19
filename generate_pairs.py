#!/usr/bin/env python3
"""Generate pairs.json by scanning the videos/ directory.

For each (game, bandwidth) we pair the real CGReplay clip with its synthetic
(RIFE frame-interpolated) counterpart. A pair is emitted only when BOTH files
exist, so the frontend never references a missing video.

  real  = {bw}Mbit_Loss0_{game}.mp4
  synth = {bw}Mbit_Loss0_interpolated_frames_rife_1600_900_{game}.mp4

Loss1 and reference_* videos are ignored.
"""
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# The three games in this study. Extend here if more are added.
GAMES = ("Forza", "Fortnite", "Kombat")

# Web-relative directory prefix used inside pairs.json (forward slashes).
WEB_PREFIX = "videos"

_GAME_ALT = "|".join(GAMES)
REAL_RE = re.compile(rf"^(\d+)Mbit_Loss0_({_GAME_ALT})\.mp4$")
SYNTH_RE = re.compile(
    rf"^(\d+)Mbit_Loss0_interpolated_frames_rife_1600_900_({_GAME_ALT})\.mp4$"
)


def find_pairs(videos_dir):
    """Return the list of available pairs, sorted by (bandwidth, game)."""
    videos_dir = Path(videos_dir)
    reals = {}   # (bw, game) -> filename
    synths = {}  # (bw, game) -> filename

    for entry in videos_dir.iterdir():
        if not entry.is_file():
            continue
        name = entry.name
        m = SYNTH_RE.fullmatch(name)
        if m:
            synths[(int(m.group(1)), m.group(2))] = name
            continue
        m = REAL_RE.fullmatch(name)
        if m:
            reals[(int(m.group(1)), m.group(2))] = name

    pairs = []
    for key in reals:
        if key not in synths:
            continue
        bw, game = key
        pairs.append({
            "id": f"{bw}Mbit_{game}",
            "game": game,
            "bandwidth_mbit": bw,
            "real": f"{WEB_PREFIX}/{reals[key]}",
            "synth": f"{WEB_PREFIX}/{synths[key]}",
        })

    pairs.sort(key=lambda p: (p["bandwidth_mbit"], p["game"]))
    return pairs


def calculate_pairs_hash(pairs):
    """Stable 16-char hash of the pair set (content, not mtime)."""
    content = "\n".join(f"{p['id']}:{p['real']}:{p['synth']}" for p in pairs)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def build_manifest(videos_dir):
    pairs = find_pairs(videos_dir)
    return {
        "version": f"1.0.{int(time.time())}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hash": calculate_pairs_hash(pairs),
        "pairs": pairs,
    }


def main():
    videos_dir = Path("videos")
    if not videos_dir.exists():
        print(f"Error: '{videos_dir}' does not exist", file=sys.stderr)
        sys.exit(1)

    manifest = build_manifest(videos_dir)
    with open("pairs.json", "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    print(f"Wrote pairs.json with {len(manifest['pairs'])} pair(s)")
    for p in manifest["pairs"]:
        print(f"  - {p['id']}")
    print(f"Version: {manifest['version']}  Hash: {manifest['hash']}")
    if len(manifest["pairs"]) < len(GAMES) * 5:
        print(
            f"Note: {len(GAMES) * 5} pairs expected once all "
            f"2/4/6/8/10 Mbit files are present."
        )


if __name__ == "__main__":
    main()
