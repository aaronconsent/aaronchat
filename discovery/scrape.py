#!/usr/bin/env python3
"""Discovery pipeline entry point.

Modes:
    --dry-run             Print the query list + cost estimate, submit nothing
    --trade <slug>        Restrict to one trade (smoke test)
    --confirm             Skip the interactive "type YES" prompt (CI / scripts)
    --resume              Skip queries whose task_id is already in output/task_log.jsonl
    --dedupe-only         Skip scrape entirely; just rebuild CSV/DB/summary from raw/

Never prints or logs OUTSCRAPER_API_KEY. Reads it once from the environment.
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
from typing import Iterable, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import config
import dedupe as dedupe_mod


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------

def _iso_now():
    return dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _log_task(row):
    """Append a JSONL row to output/task_log.jsonl so we can resume mid-run."""
    os.makedirs(os.path.dirname(config.TASK_LOG), exist_ok=True)
    with open(config.TASK_LOG, "a") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


def _load_task_log():
    if not os.path.exists(config.TASK_LOG):
        return []
    with open(config.TASK_LOG) as f:
        return [json.loads(line) for line in f if line.strip()]


def _chunk(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def _save_raw(task_id, batch_meta, response):
    """Persist per-task raw JSON so dedupe.py can rebuild output without re-paying."""
    os.makedirs(config.RAW_DIR, exist_ok=True)
    dest = os.path.join(config.RAW_DIR, f"{task_id}.json")
    with open(dest, "w") as f:
        json.dump({
            "task_id": task_id,
            "saved_at": _iso_now(),
            "batch_meta": batch_meta,
            "response": response,
        }, f, ensure_ascii=False, indent=2)
    return dest


# ---------------------------------------------------------------------------
# Dry-run: show queries + cost + wait
# ---------------------------------------------------------------------------

def print_query_plan(queries, trade_filter: Optional[str] = None):
    if trade_filter:
        queries = [q for q in queries if q["trade_slug"] == trade_filter]

    print(f"\n=== Discovery query plan ===")
    print(f"Trades:   {len({q['trade_slug'] for q in queries})}"
          + (f"  (filtered → {trade_filter})" if trade_filter else ""))
    print(f"Geo terms: {len({q['geo_key'] for q in queries})} "
          f"({len({q['county_key'] for q in queries})} counties + city breakdown)")
    print(f"Queries:  {len(queries)}")
    print(f"Batched into {(len(queries) + config.QUERIES_PER_TASK - 1) // config.QUERIES_PER_TASK} "
          f"task(s) of ≤{config.QUERIES_PER_TASK} queries.")

    est_records, est_usd = config.cost_estimate(len(queries))
    print(f"\nCost estimate")
    print(f"  Expected records: {est_records:,} "
          f"(assuming ~{config.EXPECTED_RECORDS_PER_QUERY_RURAL}/query in rural counties)")
    print(f"  At ${config.COST_PER_1000_RECORDS_USD:.2f}/1000 records → "
          f"${est_usd:.2f} USD (before dedup)")
    print(f"  Post-dedup we typically see 15-25% of the raw record count as unique "
          f"businesses.")

    print(f"\nFirst 20 queries (of {len(queries)}):")
    for q in queries[:20]:
        print(f"  [{q['trade_slug']:<20}] {q['query']}")
    if len(queries) > 20:
        print(f"  … + {len(queries) - 20} more")
    return queries


def confirm(prompt="\nType 'yes' (or YES) to submit paid tasks, anything else to abort: "):
    try:
        answer = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n[aborted]")
        return False
    return answer in ("yes", "y")


# ---------------------------------------------------------------------------
# Outscraper API — submit + poll
# ---------------------------------------------------------------------------

def get_client():
    key = os.environ.get("OUTSCRAPER_API_KEY")
    if not key:
        sys.exit("OUTSCRAPER_API_KEY missing from environment. "
                 "Export it: `export OUTSCRAPER_API_KEY=…` (never commit).")
    try:
        from outscraper import ApiClient  # official SDK
    except ImportError:
        sys.exit("Outscraper SDK missing. Install with:\n"
                 "  python3 -m pip install -r discovery/requirements.txt\n"
                 "(or `python3 -m pip install outscraper` for just this package)")
    # Never log or print the key
    return ApiClient(api_key=key)


def submit_batch(client, batch):
    """Submit up to QUERIES_PER_TASK queries as one async task. Returns task_id."""
    query_strs = [q["query"] for q in batch]
    resp = client.google_maps_search(
        query=query_strs,
        limit=config.LIMIT_PER_QUERY,
        region=config.REGION,
        language=config.LANGUAGE,
        async_request=True,
    )
    # SDK returns either a dict {'id': ...} or a str depending on version
    task_id = (resp or {}).get("id") if isinstance(resp, dict) else str(resp)
    return task_id


def poll_task(client, task_id):
    """Poll until the task is done. Returns the results payload or raises."""
    for attempt in range(config.POLL_MAX_TRIES):
        try:
            resp = client.get_request_archive(task_id)
        except Exception as ex:
            # transient — back off
            time.sleep(min(60, 5 * (2 ** min(attempt, 4))))
            continue
        status = (resp or {}).get("status")
        if status == "Success":
            return resp.get("data", [])
        if status in ("Failed", "Cancelled"):
            raise RuntimeError(f"task {task_id} status={status}: {resp}")
        # Pending / InProgress
        time.sleep(config.POLL_INTERVAL_SEC)
    raise RuntimeError(f"task {task_id} did not finish within "
                       f"{config.POLL_MAX_TRIES * config.POLL_INTERVAL_SEC}s")


def submit_and_wait_all(queries, resume=False):
    """Submit every batch, poll each, save raw JSON to output/raw/<task_id>.json.
    Returns list of raw file paths for dedupe."""
    client = get_client()

    already = set()
    if resume:
        for row in _load_task_log():
            if row.get("status") == "success":
                already.update(row.get("query_hashes", []))
        print(f"[resume] {len(already)} queries already fetched — skipping those batches.")

    def _qhash(q):
        return f"{q['trade_slug']}|{q['trade_term']}|{q['geo_key']}"

    raw_paths = []
    total_batches = (len(queries) + config.QUERIES_PER_TASK - 1) // config.QUERIES_PER_TASK
    for i, batch in enumerate(_chunk(queries, config.QUERIES_PER_TASK), start=1):
        batch = [q for q in batch if _qhash(q) not in already]
        if not batch:
            print(f"[batch {i}/{total_batches}] all queries already fetched, skipping")
            continue
        print(f"[batch {i}/{total_batches}] submitting {len(batch)} queries…")
        try:
            task_id = submit_batch(client, batch)
        except Exception as ex:
            print(f"  submit FAILED: {ex}")
            _log_task({"batch_index": i, "submitted_at": _iso_now(),
                       "status": "submit_failed", "error": str(ex)[:400],
                       "query_hashes": [_qhash(q) for q in batch]})
            time.sleep(config.SUBMIT_DELAY_SEC)
            continue

        _log_task({"batch_index": i, "task_id": task_id,
                   "submitted_at": _iso_now(), "status": "submitted",
                   "query_hashes": [_qhash(q) for q in batch]})
        print(f"  task_id={task_id} — polling…")

        try:
            data = poll_task(client, task_id)
        except Exception as ex:
            print(f"  poll FAILED: {ex}")
            _log_task({"batch_index": i, "task_id": task_id,
                       "finished_at": _iso_now(), "status": "poll_failed",
                       "error": str(ex)[:400],
                       "query_hashes": [_qhash(q) for q in batch]})
            time.sleep(config.SUBMIT_DELAY_SEC)
            continue

        path = _save_raw(task_id, batch, data)
        raw_paths.append(path)
        n_records = sum(len(sub) if isinstance(sub, list) else 0 for sub in (data or []))
        _log_task({"batch_index": i, "task_id": task_id,
                   "finished_at": _iso_now(), "status": "success",
                   "records": n_records,
                   "query_hashes": [_qhash(q) for q in batch],
                   "raw_file": path})
        print(f"  done — {n_records} records → {os.path.basename(path)}")
        time.sleep(config.SUBMIT_DELAY_SEC)

    return raw_paths


# ---------------------------------------------------------------------------
# Reclaim — try to fetch results for tasks that timed out during polling
# ---------------------------------------------------------------------------

def reclaim_failed_tasks():
    """Walk task_log.jsonl for poll_failed batches with a known task_id and
    try get_request_archive again. Outscraper may have finished the task
    after we gave up. FREE — no new tasks submitted.
    """
    log = _load_task_log()
    # Find batches whose most-recent entry is poll_failed and has a task_id
    latest_by_batch = {}
    for r in log:
        bi = r.get("batch_index")
        if bi is None:
            continue
        latest_by_batch[bi] = r
    candidates = [r for r in latest_by_batch.values()
                  if r.get("status") == "poll_failed" and r.get("task_id")]
    if not candidates:
        print("[reclaim] no poll_failed batches with a task_id to retry.")
        return []

    print(f"[reclaim] attempting to fetch results for {len(candidates)} timed-out task(s)…")
    client = get_client()
    recovered = []
    for row in candidates:
        task_id = row["task_id"]
        print(f"  batch {row['batch_index']} · task {task_id} …", end=" ", flush=True)
        try:
            resp = client.get_request_archive(task_id)
        except Exception as ex:
            print(f"error ({str(ex)[:80]})")
            continue
        status = (resp or {}).get("status")
        if status != "Success":
            print(f"still {status}")
            continue
        data = resp.get("data", [])
        # Reconstruct minimal batch_meta from query_hashes so dedupe still gets
        # per-query trade/geo attribution. Hash format: trade_slug|trade_term|geo_key
        batch_meta = []
        for qh in row.get("query_hashes", []):
            parts = qh.split("|")
            if len(parts) == 3:
                trade_slug, trade_term, geo_key = parts
            else:
                trade_slug = trade_term = geo_key = ""
            # Find county_key from geo_key by walking config
            county_key = ""
            for c in config.CITIES:
                if c["key"] == geo_key: county_key = c["county_key"]; break
            for c in config.COUNTIES:
                if c["key"] == geo_key: county_key = c["key"]; break
            batch_meta.append({
                "trade_slug": trade_slug, "trade_term": trade_term,
                "geo_key": geo_key, "county_key": county_key,
                "query": f"{trade_term} in {geo_key}",
            })
        path = _save_raw(task_id, batch_meta, data)
        n_records = sum(len(sub) if isinstance(sub, list) else 0 for sub in (data or []))
        _log_task({"batch_index": row["batch_index"], "task_id": task_id,
                   "finished_at": _iso_now(), "status": "success",
                   "records": n_records, "raw_file": path,
                   "reclaimed": True,
                   "query_hashes": row.get("query_hashes", [])})
        recovered.append(path)
        print(f"RECOVERED {n_records} records → {os.path.basename(path)}")
    print(f"[reclaim] recovered {len(recovered)}/{len(candidates)} task(s).")
    return recovered


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the query list + cost estimate, do NOT submit tasks")
    ap.add_argument("--trade", help="Restrict to one trade slug (smoke test)")
    ap.add_argument("--confirm", "--yes", "-y", dest="confirm", action="store_true",
                    help="Skip the interactive YES prompt (CI use)")
    ap.add_argument("--resume", action="store_true",
                    help="Skip batches whose queries are already in the task log")
    ap.add_argument("--dedupe-only", action="store_true",
                    help="Skip scrape; rebuild CSV/DB/summary from output/raw/")
    ap.add_argument("--reclaim", action="store_true",
                    help="For each poll_failed batch in task_log.jsonl, re-poll its "
                         "task_id (free) — Outscraper may have finished it since. "
                         "Only submits fresh tasks if reclaim fails and --resume is on.")
    args = ap.parse_args()

    queries = config.build_queries()
    if args.trade:
        valid = {t["slug"] for t in config.TRADES}
        if args.trade not in valid:
            sys.exit(f"Unknown trade slug {args.trade!r}. Valid: {sorted(valid)}")
        queries = [q for q in queries if q["trade_slug"] == args.trade]

    if args.dedupe_only:
        print("[dedupe-only] skipping scrape…")
        raw_paths = dedupe_mod.list_raw_files()
    elif args.reclaim:
        raw_paths = reclaim_failed_tasks()
        raw_paths = dedupe_mod.list_raw_files()   # include everything already saved
    else:
        print_query_plan(queries, args.trade)

        if args.dry_run:
            print("\n[dry-run] no API calls made. Re-run without --dry-run to submit.")
            return 0

        if not args.confirm and not confirm():
            print("[aborted] no tasks submitted.")
            return 1

        new_paths = submit_and_wait_all(queries, resume=args.resume)
        print(f"[scrape] {len(new_paths)} new raw file(s) written this run")
        # Always dedupe against the FULL raw/ directory so partial re-runs
        # (--resume, --reclaim, --trade) never clobber the accumulated dataset.
        raw_paths = dedupe_mod.list_raw_files()

    print(f"\n[dedupe] processing {len(raw_paths)} raw file(s)…")
    dedupe_mod.build_all(raw_paths)
    print(f"[done] wrote:")
    print(f"  {config.MASTER_CSV}")
    print(f"  {config.SQLITE_DB}")
    print(f"  {config.SUMMARY_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
