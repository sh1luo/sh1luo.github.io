#!/usr/bin/env python3
"""Keep recoverable image copies and a URL manifest, without rewriting articles."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path
from urllib.request import Request, urlopen

from check_external_images import USER_AGENT, collect_images

MAX_BYTES = 20 * 1024 * 1024


def image_extension(data: bytes) -> str:
    """Reject HTML error pages even when a host returns HTTP 200."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    if data[4:8] == b"ftyp" and data[8:12] in (b"avif", b"avis"):
        return ".avif"
    if data.lstrip().startswith(b"<"):
        try:
            if ET.fromstring(data).tag in ("svg", "{http://www.w3.org/2000/svg}svg"):
                return ".svg"
        except ET.ParseError:
            pass
    raise ValueError("response is not a recognized image")


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        try:
            output.write(data)
            output.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def verified_file(backup_dir: Path, entry: dict) -> Path | None:
    if not entry.get("file") or not entry.get("sha256"):
        return None
    path = (backup_dir / entry["file"]).resolve()
    if not path.is_relative_to(backup_dir.resolve()) or not path.is_file():
        return None
    return path if hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"] else None


def download(url: str, backup_dir: Path, timeout: float, retries: int) -> dict:
    for attempt in range(retries + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "image/*"})
            with urlopen(request, timeout=timeout) as response:
                if response.status != 200:
                    raise ValueError(f"expected full image (HTTP 200), got {response.status}")
                data = response.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    raise ValueError("image exceeds 20 MiB")
                length = response.headers.get("Content-Length")
                if length is not None and len(data) != int(length):
                    raise ValueError("incomplete image response")
            extension = image_extension(data)
            digest = hashlib.sha256(data).hexdigest()
            relative = f"objects/{digest}{extension}"
            atomic_write(backup_dir / relative, data)
            return {
                "file": relative,
                "sha256": digest,
                "bytes": len(data),
                "savedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        except (OSError, ValueError, HTTPException) as error:
            if attempt == retries:
                raise ValueError(str(error)) from error
            time.sleep(1 + attempt)
    raise AssertionError("unreachable")


def backup(content_dir: Path, backup_dir: Path, manifest: dict, workers: int, timeout: float, retries: int) -> int:
    references = collect_images(content_dir)
    entries = manifest["images"]
    pending = []
    for url, sources in references.items():
        entry = entries.setdefault(url, {})
        entry["sources"] = sorted(sources)
        if verified_file(backup_dir, entry) is None:
            pending.append(url)
        else:
            entry.pop("lastError", None)

    failures = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(download, url, backup_dir, timeout, retries): url for url in pending}
        for future in as_completed(futures):
            url = futures[future]
            try:
                entries[url].update(future.result())
                entries[url].pop("lastError", None)
                print(f"SAVED {url}", flush=True)
            except ValueError as error:
                failures += 1
                entries[url]["lastError"] = str(error)
                print(f"FAILED {url}: {error}", file=sys.stderr, flush=True)

    atomic_write(backup_dir / "manifest.json", (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode())
    print(f"Backed up {len(references) - failures}/{len(references)} referenced images; {failures} missing.")
    return int(failures > 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("content_dir", nargs="?", default="content")
    parser.add_argument("--backup-dir", type=Path, default=Path("backups/external-images"))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--retries", type=int, default=1)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="check all saved hashes and report missing backups, offline")
    mode.add_argument("--restore", metavar="URL", help="restore one image from the manifest, offline")
    parser.add_argument("--output", type=Path, help="destination for --restore; must not exist")
    args = parser.parse_args()
    if bool(args.restore) != bool(args.output):
        parser.error("--restore and --output must be used together")
    if args.workers < 1 or args.timeout <= 0 or args.retries < 0:
        parser.error("workers/timeout must be positive; retries must be nonnegative")

    manifest_path = args.backup_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"version": 1, "images": {}}
        if manifest.get("version") != 1 or not isinstance(manifest.get("images"), dict):
            raise ValueError("unsupported backup manifest")
        if args.restore:
            source = verified_file(args.backup_dir, manifest["images"].get(args.restore, {}))
            if source is None:
                raise ValueError("no verified backup for this URL")
            with args.output.open("xb") as output:
                output.write(source.read_bytes())
            print(f"Restored {args.output}")
            return 0
        if args.verify:
            if not manifest_path.exists():
                raise ValueError("backup manifest does not exist")
            content_dir = Path(args.content_dir)
            if not content_dir.is_dir():
                raise ValueError(f"content directory does not exist: {content_dir}")
            urls = set(manifest["images"]) | set(collect_images(content_dir))
            missing = sorted(url for url in urls if verified_file(args.backup_dir, manifest["images"].get(url, {})) is None)
            for url in missing:
                print(f"MISSING OR CORRUPT {url}", file=sys.stderr)
            if missing:
                print("Run make backup-images to save missing images or repair corrupt copies.", file=sys.stderr)
            print(f"Verified {len(urls) - len(missing)}/{len(urls)} backups.")
            return int(bool(missing))
        content_dir = Path(args.content_dir)
        if not content_dir.is_dir():
            raise ValueError(f"content directory does not exist: {content_dir}")
        return backup(content_dir, args.backup_dir, manifest, args.workers, args.timeout, args.retries)
    except (OSError, ValueError) as error:
        print(f"Backup error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
