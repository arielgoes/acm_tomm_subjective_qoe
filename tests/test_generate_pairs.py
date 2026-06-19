"""Unit tests for generate_pairs.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import generate_pairs as gp


def _touch(d: Path, name: str) -> None:
    (d / name).write_bytes(b"\x00")


def _make_pair(d: Path, bw: int, game: str) -> None:
    _touch(d, f"{bw}Mbit_Loss0_{game}.mp4")
    _touch(d, f"{bw}Mbit_Loss0_interpolated_frames_rife_1600_900_{game}.mp4")


def test_find_pairs_basic(tmp_path):
    _make_pair(tmp_path, 4, "Forza")
    _make_pair(tmp_path, 10, "Fortnite")

    pairs = gp.find_pairs(tmp_path)

    assert len(pairs) == 2
    forza = next(p for p in pairs if p["id"] == "4Mbit_Forza")
    assert forza["game"] == "Forza"
    assert forza["bandwidth_mbit"] == 4
    assert forza["real"] == "videos/4Mbit_Loss0_Forza.mp4"
    assert forza["synth"] == (
        "videos/4Mbit_Loss0_interpolated_frames_rife_1600_900_Forza.mp4"
    )


def test_pair_requires_both_files(tmp_path):
    # real only
    _touch(tmp_path, "6Mbit_Loss0_Kombat.mp4")
    # synth only (different bw/game)
    _touch(tmp_path, "8Mbit_Loss0_interpolated_frames_rife_1600_900_Forza.mp4")

    assert gp.find_pairs(tmp_path) == []


def test_ignores_reference_and_unknown(tmp_path):
    _make_pair(tmp_path, 2, "Kombat")
    _touch(tmp_path, "reference_video_Kombat_1600x900_frames.mp4")
    _touch(tmp_path, "random.mp4")
    _touch(tmp_path, "notes.txt")

    pairs = gp.find_pairs(tmp_path)
    assert [p["id"] for p in pairs] == ["2Mbit_Kombat"]


def test_ignores_loss1(tmp_path):
    _make_pair(tmp_path, 4, "Forza")
    _touch(tmp_path, "4Mbit_Loss1_Forza.mp4")
    _touch(tmp_path, "4Mbit_Loss1_interpolated_frames_rife_1600_900_Forza.mp4")

    pairs = gp.find_pairs(tmp_path)
    assert [p["id"] for p in pairs] == ["4Mbit_Forza"]


def test_sorted_by_bandwidth_then_game(tmp_path):
    _make_pair(tmp_path, 10, "Forza")
    _make_pair(tmp_path, 2, "Kombat")
    _make_pair(tmp_path, 2, "Forza")

    ids = [p["id"] for p in gp.find_pairs(tmp_path)]
    assert ids == ["2Mbit_Forza", "2Mbit_Kombat", "10Mbit_Forza"]


def test_hash_stable_and_sensitive(tmp_path):
    _make_pair(tmp_path, 4, "Forza")
    h1 = gp.calculate_pairs_hash(gp.find_pairs(tmp_path))
    h2 = gp.calculate_pairs_hash(gp.find_pairs(tmp_path))
    assert h1 == h2 and len(h1) == 16

    _make_pair(tmp_path, 6, "Fortnite")
    h3 = gp.calculate_pairs_hash(gp.find_pairs(tmp_path))
    assert h3 != h1


def test_build_manifest_shape(tmp_path):
    _make_pair(tmp_path, 4, "Forza")
    manifest = gp.build_manifest(tmp_path)

    assert set(manifest) == {"version", "generated_at", "hash", "pairs"}
    assert manifest["version"].startswith("1.0.")
    assert len(manifest["pairs"]) == 1
