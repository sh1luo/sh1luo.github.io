#!/usr/bin/env python3
"""Check externally hosted images referenced by Markdown content."""

from __future__ import annotations

import argparse
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MARKDOWN_IMAGE = re.compile(
    r"!\[[^\]]*\]\((https?://(?:[^\s()]|\([^)]*\))+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\)"
)
HTML_IMAGE = re.compile(r"<img\b[^>]*\bsrc=['\"](https?://[^'\"]+)", re.IGNORECASE)
USER_AGENT = "WasabiLinkCheck/1.0 (+https://sh1luo.github.io/)"


def collect_images(content_dir: Path) -> dict[str, set[str]]:
    references: dict[str, set[str]] = {}
    for markdown_file in sorted(content_dir.rglob("*.md")):
        text = markdown_file.read_text(encoding="utf-8")
        for pattern in (MARKDOWN_IMAGE, HTML_IMAGE):
            for url in pattern.findall(text):
                references.setdefault(url, set()).add(markdown_file.as_posix())
    return references


def check_url(url: str, timeout: float, retries: int) -> tuple[bool, str]:
    last_error = "unknown error"
    for attempt in range(retries + 1):
        request = Request(
            url,
            headers={
                "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
                "Range": "bytes=0-0",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                response.read(1)
                status = getattr(response, "status", 200)
                if 200 <= status < 400:
                    return True, str(status)
                last_error = f"HTTP {status}"
        except HTTPError as error:
            last_error = f"HTTP {error.code}"
        except (TimeoutError, URLError, OSError) as error:
            last_error = str(error.reason if isinstance(error, URLError) else error)

        if attempt < retries:
            time.sleep(1.0 + attempt)

    return False, last_error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("content_dir", nargs="?", default="content")
    parser.add_argument("--list", action="store_true", help="list URLs without network requests")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()

    content_dir = Path(args.content_dir).resolve()
    if not content_dir.is_dir():
        print(f"Content directory does not exist: {content_dir}", file=sys.stderr)
        return 2

    references = collect_images(content_dir)
    print(f"Found {len(references)} unique external images.")
    if args.list:
        for url in sorted(references):
            print(url)
        return 0

    failures: list[tuple[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(check_url, url, args.timeout, max(0, args.retries)): url
            for url in references
        }
        for future in as_completed(futures):
            url = futures[future]
            ok, result = future.result()
            print(f"{'OK' if ok else 'FAIL'} {result} {url}")
            if not ok:
                failures.append((url, result))

    if failures:
        print("\nUnavailable external images:", file=sys.stderr)
        for url, reason in sorted(failures):
            sources = ", ".join(sorted(references[url]))
            print(f"  {reason}: {url} ({sources})", file=sys.stderr)
        return 1

    print("All external images are reachable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
