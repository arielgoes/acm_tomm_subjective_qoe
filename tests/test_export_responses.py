"""Unit tests for export_responses.rows_to_csv / order_columns."""
import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import export_responses as ex


SAMPLE = [
    {
        "id": 1, "created_at": "2026-06-19T18:00:00Z", "participant_id": "abc",
        "pair_id": "4Mbit_Forza", "game": "Forza", "bandwidth_mbit": 4,
        "pair_index": 0, "video_a_kind": "real", "video_b_kind": "synth",
        "video_a_file": "videos/4Mbit_Loss0_Forza.mp4",
        "video_b_file": "videos/4Mbit_Loss0_interpolated_frames_rife_1600_900_Forza.mp4",
        "score_a": 5, "score_b": 3, "which_real": "Video A", "is_correct": True,
        "pairs_version": "1.0.1", "pairs_hash": "deadbeef",
        "user_agent": "Mozilla/5.0 (X11; Linux)",
    },
    {
        "id": 2, "created_at": "2026-06-19T18:01:00Z", "participant_id": "abc",
        "pair_id": "4Mbit_Kombat", "game": "Kombat", "bandwidth_mbit": 4,
        "pair_index": 1, "video_a_kind": "synth", "video_b_kind": "real",
        "video_a_file": "x", "video_b_file": "y",
        "score_a": 2, "score_b": 4, "which_real": "None", "is_correct": False,
        "pairs_version": "1.0.1", "pairs_hash": "deadbeef",
        "user_agent": 'has,comma "and quote"',
    },
]


def _parse(csv_text):
    return list(csv.reader(io.StringIO(csv_text)))


def test_header_matches_schema_order():
    rows = _parse(ex.rows_to_csv(SAMPLE))
    assert rows[0] == ex.COLUMNS
    assert len(rows) == 3  # header + 2 data rows


def test_values_roundtrip_and_escaping():
    rows = _parse(ex.rows_to_csv(SAMPLE))
    # csv.reader transparently unescapes the quoted field with comma + quotes
    ua_idx = ex.COLUMNS.index("user_agent")
    assert rows[2][ua_idx] == 'has,comma "and quote"'
    correct_idx = ex.COLUMNS.index("is_correct")
    assert rows[1][correct_idx] == "True"
    assert rows[2][correct_idx] == "False"


def test_empty_rows_header_only():
    out = ex.rows_to_csv([], columns=ex.COLUMNS)
    rows = _parse(out)
    assert rows == [ex.COLUMNS]


def test_none_becomes_empty_string():
    out = ex.rows_to_csv([{"id": 1, "game": None}], columns=["id", "game"])
    rows = _parse(out)
    assert rows[1] == ["1", ""]


def test_extra_keys_appended_sorted():
    cols = ex.order_columns([{"id": 1, "zeta": 1, "alpha": 2}])
    assert cols[:len(ex.COLUMNS)] == ex.COLUMNS
    assert cols[len(ex.COLUMNS):] == ["alpha", "zeta"]


def test_auth_headers_new_secret_key_no_bearer():
    h = ex.auth_headers("sb_secret_abc123")
    assert h["apikey"] == "sb_secret_abc123"
    assert "Authorization" not in h


def test_auth_headers_legacy_jwt_uses_bearer():
    jwt = "eyJhbGciOiJIUzI1Ni'"
    h = ex.auth_headers(jwt)
    assert h["apikey"] == jwt
    assert h["Authorization"] == f"Bearer {jwt}"
