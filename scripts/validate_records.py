#!/usr/bin/env python3
"""Validate a collection JSON file without project-specific dependencies."""

import argparse
import json
import re
import sys
from collections import Counter
from urllib.parse import parse_qsl, urlencode, urldefrag, urlparse, urlunparse

ALLOWED = {"ok", "restricted", "no_body", "error"}
FIRMS = {"mckinsey.com": "McKinsey", "bcg.com": "BCG", "bain.com": "Bain"}


def canonical_url(value):
    raw = str(value or "").strip()
    parsed = urlparse(urldefrag(raw)[0])
    query = [(key, val) for key, val in parse_qsl(parsed.query, keep_blank_values=True)
             if not key.lower().startswith("utm_") and key.lower() != "gclid"]
    path = re.sub(r"/+", "/", parsed.path).rstrip("/") or "/"
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", urlencode(query), ""))


def official_firm(url):
    host = urlparse(url).netloc.lower().split(":")[0]
    for domain, firm in FIRMS.items():
        if host == domain or host.endswith("." + domain):
            return firm
    return ""


def load_items(path):
    payload = json.load(open(path, encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("records") or payload.get("items") or payload.get("data") or []
    return payload if isinstance(payload, list) else []


def validate(item, min_body_chars):
    errors = []
    url = canonical_url(item.get("source_url") or item.get("url") or item.get("final_url"))
    body = str(item.get("body_text") or "")
    firm = official_firm(url)
    if not url.startswith("https://"):
        errors.append("source_url must use https")
    if not firm:
        errors.append("source_url is outside official MBB domains")
    if firm and item.get("firm") != firm:
        errors.append("firm does not match official domain")
    if item.get("status") not in ALLOWED:
        errors.append("unknown status")
    if item.get("status") == "ok" and len(body.strip()) < min_body_chars:
        errors.append("ok body is shorter than minimum")
    if item.get("body_chars") not in (None, len(body)):
        errors.append("body_chars does not match body_text")
    if not str(item.get("title") or "").strip():
        errors.append("title is empty")
    return errors, url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="fetched.json or records.json")
    parser.add_argument("--min-body-chars", type=int, default=800)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    items = load_items(args.input)
    counts = Counter()
    seen = set()
    invalid = []
    for index, item in enumerate(items):
        errors, url = validate(item, args.min_body_chars)
        counts[str(item.get("status") or "missing")] += 1
        if url in seen and url:
            errors.append("duplicate canonical source_url")
        if url:
            seen.add(url)
        if errors:
            invalid.append({"index": index, "url": url, "errors": errors})
    result = {"record_count": len(items), "unique_url_count": len(seen), "status_counts": dict(counts), "invalid_count": len(invalid), "invalid": invalid}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if args.strict and invalid else 0


if __name__ == "__main__":
    sys.exit(main())
