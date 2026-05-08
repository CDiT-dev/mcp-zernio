"""Probe Zernio's /v1/posts endpoint to find the correct thread payload shape.

Usage:
    ZERNIO_API_KEY=... uv run python scripts/probe_thread_payload.py

Tries 4 candidate payload shapes against Zernio. Creates DRAFTS (publishNow=False),
collects post IDs of any that succeed, and DELETES them at the end.

Variant shapes tried:
    A: content = first item, threadItems = items[1:]
    B: content = first item (dup), threadItems = all items
    C: content = "" (current MCP code, expected to fail)
    D: top-level threadItems (no platformSpecificData wrapping)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

import httpx

API_KEY = os.environ.get("ZERNIO_API_KEY")
if not API_KEY:
    print("ERROR: set ZERNIO_API_KEY in env", file=sys.stderr)
    sys.exit(1)

BASE = os.environ.get("ZERNIO_API_BASE", "https://zernio.com/api")
TWITTER_ACC = "69c2d4a36cb7b8cf4c96ed4a"
BLUESKY_ACC = "69c2d4596cb7b8cf4c96ebfe"

ITEMS = [
    {"content": "PROBE 1/2 — payload shape test (draft, will delete). Ignore."},
    {"content": "PROBE 2/2 — payload shape test (draft, will delete). Ignore."},
]

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def variant_a():
    """content = first item, threadItems = items[1:]"""
    return {
        "content": ITEMS[0]["content"],
        "platforms": [
            {
                "platform": "twitter",
                "accountId": TWITTER_ACC,
                "platformSpecificData": {"threadItems": ITEMS[1:]},
            },
            {
                "platform": "bluesky",
                "accountId": BLUESKY_ACC,
                "platformSpecificData": {"threadItems": ITEMS[1:]},
            },
        ],
    }


def variant_b():
    """content = first item, threadItems = all items (current MCP shape but with content set)"""
    return {
        "content": ITEMS[0]["content"],
        "platforms": [
            {
                "platform": "twitter",
                "accountId": TWITTER_ACC,
                "platformSpecificData": {"threadItems": ITEMS},
            },
            {
                "platform": "bluesky",
                "accountId": BLUESKY_ACC,
                "platformSpecificData": {"threadItems": ITEMS},
            },
        ],
    }


def variant_c():
    """content = '' (current MCP code, expected 400)"""
    return {
        "content": "",
        "platforms": [
            {
                "platform": "twitter",
                "accountId": TWITTER_ACC,
                "platformSpecificData": {"threadItems": ITEMS},
            },
            {
                "platform": "bluesky",
                "accountId": BLUESKY_ACC,
                "platformSpecificData": {"threadItems": ITEMS},
            },
        ],
    }


def variant_d():
    """Top-level threadItems instead of per-platform"""
    return {
        "content": ITEMS[0]["content"],
        "threadItems": ITEMS,
        "platforms": [
            {"platform": "twitter", "accountId": TWITTER_ACC},
            {"platform": "bluesky", "accountId": BLUESKY_ACC},
        ],
    }


VARIANTS = [
    ("A: content=first, threadItems=rest (per-platform)", variant_a),
    ("B: content=first, threadItems=all (per-platform)", variant_b),
    ("C: content='', threadItems=all (current MCP shape)", variant_c),
    ("D: top-level threadItems", variant_d),
]


async def probe():
    created_ids: list[str] = []
    results: list[dict] = []

    async with httpx.AsyncClient(timeout=30) as cx:
        for label, build in VARIANTS:
            body = build()
            try:
                r = await cx.post(f"{BASE}/v1/posts", json=body, headers=HEADERS)
                status = r.status_code
                try:
                    data = r.json()
                except Exception:
                    data = {"raw": r.text[:300]}
            except Exception as e:
                status, data = -1, {"exception": str(e)}

            ok = status == 200 or status == 201
            post_id = None
            if ok and isinstance(data, dict):
                post_id = data.get("post", {}).get("_id") or data.get("_id")
                if post_id:
                    created_ids.append(post_id)

            # Inspect the saved post structure if it succeeded
            saved_shape = None
            if ok and isinstance(data, dict):
                post = data.get("post", data)
                saved_shape = {
                    "content": (post.get("content") or "")[:60],
                    "platforms": [
                        {
                            "platform": p.get("platform"),
                            "psd_keys": list((p.get("platformSpecificData") or {}).keys()),
                            "threadItems_len": len((p.get("platformSpecificData") or {}).get("threadItems") or []),
                        }
                        for p in (post.get("platforms") or [])
                    ],
                }

            results.append(
                {
                    "variant": label,
                    "status": status,
                    "ok": ok,
                    "post_id": post_id,
                    "error": data.get("error") if isinstance(data, dict) else None,
                    "saved_shape": saved_shape,
                }
            )
            print(f"\n=== {label} ===")
            print(f"  status: {status}  ok: {ok}")
            if not ok:
                print(f"  error:  {json.dumps(data)[:300]}")
            else:
                print(f"  post_id: {post_id}")
                print(f"  saved_shape: {json.dumps(saved_shape, indent=2)}")

        # Cleanup
        print(f"\n--- Cleaning up {len(created_ids)} drafts ---")
        for pid in created_ids:
            try:
                r = await cx.delete(f"{BASE}/v1/posts/{pid}", headers=HEADERS)
                print(f"  deleted {pid}: {r.status_code}")
            except Exception as e:
                print(f"  delete {pid} FAILED: {e}")

    print("\n\n=== SUMMARY ===")
    for r in results:
        marker = "✅" if r["ok"] else "❌"
        print(f"{marker} {r['variant']}: HTTP {r['status']}")
        if r["saved_shape"]:
            for p in r["saved_shape"]["platforms"]:
                print(f"     - {p['platform']}: psd_keys={p['psd_keys']}, threadItems_len={p['threadItems_len']}")


if __name__ == "__main__":
    asyncio.run(probe())
