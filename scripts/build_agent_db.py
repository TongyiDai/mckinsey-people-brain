#!/usr/bin/env python3
"""Build deterministic JSON, CSV and SQLite outputs from fetched records."""

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urldefrag, urlparse, urlunparse

ALLOWED = {"ok", "restricted", "no_body", "error"}
FIRMS = {"mckinsey.com": "McKinsey", "bcg.com": "BCG", "bain.com": "Bain"}
THEMES = [
    ("AI 与未来工作", ("agentic", "generative ai", "artificial intelligence", "future of work", "automation", "ai/")),
    ("技能与学习", ("skill", "capabilit", "learning", "upskill", "reskill", "技能", "学习")),
    ("绩效与激励", ("performance management", "performance", "incentive", "reward")),
    ("People Analytics", ("people analytics", "hr analytics", "workforce analytics")),
    ("员工体验与文化", ("employee experience", "engagement", "culture", "employee listening")),
    ("领导力与管理", ("leadership", "leader", "chro", "manager")),
    ("劳动力规划与招聘", ("workforce planning", "workforce", "recruit", "talent market")),
    ("人才战略与组织设计", ("talent strategy", "talent management", "organization", "operating model", "people strategy")),
]


def canonical_url(value):
    raw = str(value or "").strip()
    parsed = urlparse(urldefrag(raw)[0])
    query = [(key, val) for key, val in parse_qsl(parsed.query, keep_blank_values=True)
             if not key.lower().startswith("utm_") and key.lower() != "gclid"]
    path = re.sub(r"/+", "/", parsed.path).rstrip("/") or "/"
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", urlencode(query), ""))


def firm_for(url):
    host = urlparse(url).netloc.lower().split(":")[0]
    for domain, firm in FIRMS.items():
        if host == domain or host.endswith("." + domain):
            return firm
    return ""


def load(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("records") or payload.get("items") or payload.get("data") or []
    return payload if isinstance(payload, list) else []


def normalize(raw):
    url = canonical_url(raw.get("source_url") or raw.get("url") or raw.get("final_url"))
    body = str(raw.get("body_text") or "")
    item = dict(raw)
    item.update({
        "id": raw.get("id") or hashlib.sha256(url.encode("utf-8")).hexdigest()[:16],
        "firm": raw.get("firm") or firm_for(url),
        "title": str(raw.get("title") or "").strip(),
        "source_url": url,
        "final_url": canonical_url(raw.get("final_url") or url),
        "published_date": str(raw.get("published_date") or "")[:10],
        "body_text": body,
        "body_chars": len(body),
        "tags": list(raw.get("tags") or []),
        "themes": list(raw.get("themes") or []),
    })
    return item


def theme_for(item):
    hay = " ".join([item.get("title", ""), item.get("source_url", ""), " ".join(item.get("tags", [])), item.get("body_text", "")[:2000]]).lower()
    for theme, tokens in THEMES:
        if any(token in hay for token in tokens):
            return theme
    return "人才战略与组织设计"


def quality_errors(item, minimum):
    errors = []
    expected = firm_for(item["source_url"])
    if not item["source_url"].startswith("https://") or not expected:
        errors.append("source_url is not an official https MBB URL")
    if expected and item["firm"] != expected:
        errors.append("firm mismatch")
    if item.get("status") not in ALLOWED:
        errors.append("unknown status")
    if item.get("status") == "ok" and len(item["body_text"].strip()) < minimum:
        errors.append("ok body below minimum")
    if not item["title"]:
        errors.append("title is empty")
    return errors


def better(old, new):
    rank = {"ok": 4, "no_body": 3, "restricted": 2, "error": 1}
    old_key = (rank.get(old.get("status"), 0), len(old.get("body_text", "")), bool(old.get("title")), old.get("fetched_at_utc", ""))
    new_key = (rank.get(new.get("status"), 0), len(new.get("body_text", "")), bool(new.get("title")), new.get("fetched_at_utc", ""))
    return new if new_key > old_key else old


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def build_sqlite(path, items):
    if path.exists():
        path.unlink()
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE records(rowid INTEGER PRIMARY KEY, id TEXT UNIQUE, firm TEXT, title TEXT, published_date TEXT, status TEXT, source_url TEXT UNIQUE, body_chars INTEGER, body_text TEXT, tags TEXT, themes TEXT, failure_reason TEXT, fetched_at_utc TEXT, duplicate_of TEXT)")
    db.execute("CREATE INDEX idx_records_firm_status ON records(firm, status)")
    db.execute("CREATE INDEX idx_records_date ON records(published_date)")
    fts = True
    try:
        db.execute("CREATE VIRTUAL TABLE records_fts USING fts5(title, firm, tags, themes, body_text, content='records', content_rowid='rowid')")
    except sqlite3.OperationalError:
        fts = False
    for item in items:
        cur = db.execute("INSERT INTO records(id,firm,title,published_date,status,source_url,body_chars,body_text,tags,themes,failure_reason,fetched_at_utc,duplicate_of) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (item["id"], item["firm"], item["title"], item.get("published_date", ""), item.get("status", "error"), item["source_url"], item["body_chars"], item["body_text"], "; ".join(item.get("tags", [])), "; ".join(item.get("themes", [])), item.get("failure_reason", ""), item.get("fetched_at_utc", ""), item.get("duplicate_of", "")))
        if fts:
            db.execute("INSERT INTO records_fts(rowid,title,firm,tags,themes,body_text) VALUES(?,?,?,?,?,?)", (cur.lastrowid, item["title"], item["firm"], "; ".join(item.get("tags", [])), "; ".join(item.get("themes", [])), item["body_text"]))
    db.commit()
    db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--base-corpus", type=Path)
    parser.add_argument("--min-body-chars", type=int, default=800)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    fetched = args.run_dir / "fetched.json"
    if not fetched.exists():
        raise SystemExit("missing collection output: " + str(fetched))
    raw = (load(args.base_corpus) if args.base_corpus else []) + load(fetched)
    by_url = {}
    for entry in raw:
        item = normalize(entry)
        if not item["source_url"]:
            continue
        by_url[item["source_url"]] = better(by_url[item["source_url"]], item) if item["source_url"] in by_url else item
    items = []
    invalid_count = 0
    for item in by_url.values():
        errors = quality_errors(item, args.min_body_chars)
        if errors:
            invalid_count += 1
            if item.get("status") == "ok":
                item["status"] = "error"
            item["failure_reason"] = "; ".join(errors)
        item["themes"] = [theme_for(item)]
        items.append(item)
    items.sort(key=lambda x: (x.get("firm", ""), x.get("published_date", ""), x.get("title", "")), reverse=True)
    out = args.run_dir / "agent-db"
    atomic_json(out / "records.json", items)
    fields = ["id", "firm", "title", "published_date", "status", "body_chars", "source_url", "themes", "tags", "failure_reason"]
    with (out / "source-register.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in items:
            row = dict(item)
            row["themes"] = "; ".join(item.get("themes", []))
            row["tags"] = "; ".join(item.get("tags", []))
            writer.writerow({field: row.get(field, "") for field in fields})
    build_sqlite(out / "agent-db.sqlite", items)
    manifest = {"built_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "record_count": len(items), "invalid_records": invalid_count, "firm_counts": dict(Counter(item.get("firm", "") for item in items)), "status_counts": dict(Counter(item.get("status", "") for item in items)), "outputs": {"json": "records.json", "csv": "source-register.csv", "sqlite": "agent-db.sqlite"}}
    atomic_json(out / "manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 1 if args.strict and invalid_count else 0


if __name__ == "__main__":
    sys.exit(main())
