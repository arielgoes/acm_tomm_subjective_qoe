#!/usr/bin/env python3
"""Export all responses from Supabase to a CSV file for offline analysis.

Reads credentials from the environment (or --url / --key):

    SUPABASE_URL          e.g. https://xxxx.supabase.co
    SUPABASE_SERVICE_KEY  the service_role key (NOT the anon key) -- it bypasses
                          RLS so it can read the append-only table. Keep it secret.

Usage:
    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python export_responses.py
    python export_responses.py --url https://xxxx.supabase.co --key <service_key>
"""
import argparse
import csv
import io
import os
import sys

TABLE = "responses"
PAGE_SIZE = 1000

# Preferred column order (schema order). Any unexpected keys are appended.
COLUMNS = [
    "id", "created_at", "participant_id", "pair_id", "game", "bandwidth_mbit",
    "pair_index", "video_a_kind", "video_b_kind", "video_a_file", "video_b_file",
    "score_a", "score_b", "which_real", "is_correct", "pairs_version",
    "pairs_hash", "user_agent",
]


def order_columns(rows):
    """Stable column list: COLUMNS first, then any extra keys (sorted)."""
    extras = set()
    for r in rows:
        extras.update(r.keys())
    extras.difference_update(COLUMNS)
    return COLUMNS + sorted(extras)


def rows_to_csv(rows, columns=None):
    """Render a list of dict rows to a CSV string."""
    columns = columns or order_columns(rows)
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(columns)
    for r in rows:
        writer.writerow(["" if r.get(c) is None else r.get(c) for c in columns])
    return buf.getvalue()


def fetch_all_rows(url, key):
    """Fetch every row from the responses table, paginating as needed."""
    import requests

    base = url.rstrip("/") + f"/rest/v1/{TABLE}"
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    rows, offset = [], 0
    while True:
        resp = requests.get(
            base,
            headers=headers,
            params={"select": "*", "order": "id.asc",
                    "limit": PAGE_SIZE, "offset": offset},
            timeout=60,
        )
        resp.raise_for_status()
        batch = resp.json()
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def main():
    parser = argparse.ArgumentParser(description="Export QoE responses to CSV.")
    parser.add_argument("--url", default=os.environ.get("SUPABASE_URL"))
    parser.add_argument("--key", default=os.environ.get("SUPABASE_SERVICE_KEY"))
    parser.add_argument("--output", default="responses_export.csv")
    args = parser.parse_args()

    if not args.url or not args.key:
        print("Error: set SUPABASE_URL and SUPABASE_SERVICE_KEY (or pass "
              "--url/--key).", file=sys.stderr)
        sys.exit(1)

    rows = fetch_all_rows(args.url, args.key)
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        f.write(rows_to_csv(rows))
    print(f"Exported {len(rows)} row(s) to {args.output}")


if __name__ == "__main__":
    main()
