# ACM TOMM — Subjective QoE Evaluation

A subjective video-quality study where participants compare **real** CGReplay
gameplay clips against **synthetic** (RIFE frame-interpolated) versions of the
same clip, and try to tell them apart. Static site, hosted on GitHub Pages.

Each participant gets a random ID, then evaluates **all 15 pairs**
(3 games × 5 bandwidths) in an order shuffled per-participant. For each pair they
rate both videos 1–5 (MOS) and answer one question: **"Which videos do you think
are real?"** (`None / Both / Video A / Video B`).

## How it works

| File | Role |
|---|---|
| `index.html` | Landing → evaluation → thank-you. Vanilla JS, no build step. |
| `stats.html` | Online dashboard — live charts from the `response_stats` view. |
| `config.js` | Supabase URL + publishable key. Empty = **local mode** (CSV download). |
| `pairs.json` | **Auto-generated** manifest of available pairs. |
| `generate_pairs.py` | Scans `videos/`, writes `pairs.json`. |
| `supabase_schema.sql` | Creates the append-only `responses_acm_tomm_subjective_qoe` table + RLS policy. |
| `export_responses.py` | Pulls all rows from Supabase into a CSV. |
| `app.py` | Tiny local static server for testing. |
| `videos/` | The `.mp4` clips. |
| `tests/` | `pytest` unit tests for the Python pieces. |

### Pairing rule

For each `(game, bandwidth)`:

- real  = `{bw}Mbit_Loss0_{game}.mp4`
- synth = `{bw}Mbit_Loss0_interpolated_frames_rife_1600_900_{game}.mp4`

A pair appears in `pairs.json` only when **both** files exist. `Loss1` and
`reference_*` videos are ignored. Games: Forza, Fortnite, Kombat. Bandwidths:
2/4/6/8/10 Mbit → 15 pairs once all videos are present.

### Determinism

- Pair **order** and which side (A/B) shows the real vs synth clip are both
  derived from a hash of the participant ID, so the layout is reproducible per
  participant but unpredictable across participants (no "A is always real").
- The true side is recorded, and `is_correct` is computed at save time.

## Local testing (no backend)

```bash
python generate_pairs.py          # (re)build pairs.json
python app.py                     # serve http://localhost:8000
```

Open <http://localhost:8000>, complete a session. With `config.js` empty, every
response is stored in the browser and you can **Download CSV** on the thank-you
screen.

Run the unit tests:

```bash
pip install -r requirements.txt
pytest -q
```

## Online collection with Supabase

1. Create a free project at <https://supabase.com>.
2. **SQL Editor → New query →** paste `supabase_schema.sql` → Run. This grants
   `anon` INSERT, enables RLS, and adds an **insert-only** policy (both layers are
   required — a grant controls table access, RLS controls row access).
3. **Project Settings → API Keys**: copy the **Project URL** and the
   **publishable** key (`sb_publishable_…`) into `config.js`:

   ```js
   window.SUPABASE_URL = "https://xxxx.supabase.co";
   window.SUPABASE_PUBLISHABLE_KEY = "sb_publishable_...";  // safe to expose
   ```

   The publishable key is meant to be public; with the grant + insert-only RLS
   policy, participants can only append rows — never read, edit, or delete.
   (A legacy `anon` JWT key also works — set `window.SUPABASE_ANON_KEY` instead.)
4. Commit and push. The site posts each pair's response directly to Supabase
   (with a localStorage mirror as backup).

### Exporting the data

```bash
export SUPABASE_URL="https://xxxx.supabase.co"
export SUPABASE_SECRET_KEY="sb_secret_..."   # Settings → API Keys, keep secret
python export_responses.py                    # -> responses_export.csv
```

The **secret** key (`sb_secret_…`, or a legacy `service_role` JWT) bypasses RLS so
the script can read the table. Never put it in `config.js` or any client-side
file. Set it via the environment (`.env` is git-ignored).

## Online stats dashboard (`stats.html`)

`stats.html` renders live charts (Chart.js) of mean MOS (real vs synth) and
detection accuracy, broken down by bandwidth and game, plus an aggregate table.
Charts read the `response_stats` aggregate view; a **Download all responses
(CSV)** button pulls the full raw table client-side (paginated).

This study publishes raw responses as **open data** — the schema grants `anon`
both `insert` and `select` on the table (no PII is collected). The table stays
append-only (no update/delete for `anon`). If you'd rather keep raw data private,
drop the `anon read responses` policy + `grant select` on the table and the
dashboard charts still work from the view alone (but the CSV download won't).

The dashboard is linked from the landing page's **View Statistics Dashboard**
button. No data yet → it shows "No responses yet."

## Deployment (GitHub Pages)

- `.github/workflows/static.yml` deploys the repo to Pages on every push to
  `main` (enable Pages → Source: GitHub Actions in repo settings).
- `.github/workflows/update_pairs.yml` regenerates and commits `pairs.json`
  whenever `videos/**` changes — so adding the remaining bandwidths is just
  dropping the files into `videos/`.
