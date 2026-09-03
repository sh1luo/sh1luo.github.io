#!/usr/bin/env python3
"""Fail when generated pages reference a missing local target or fragment."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


SITE_ORIGIN = "https://sh1luo.github.io"
LINK_ATTRIBUTES = {
    "a": ("href",),
    "audio": ("src",),
    "iframe": ("src",),
    "img": ("src", "srcset"),
    "link": ("href",),
    "script": ("src",),
    "source": ("src", "srcset"),
    "video": ("src", "poster"),
}
IGNORED_SCHEMES = {"data", "javascript", "mailto", "tel"}
CSS_URL_PATTERN = re.compile(r"url\(\s*['\"]?([^'\")]+)")


def srcset_urls(value: str) -> list[str]:
    return [candidate.strip().split()[0] for candidate in value.split(",") if candidate.strip()]


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name: value for name, value in attrs if value is not None}
        if element_id := values.get("id"):
            self.ids.add(element_id)
        if anchor_name := values.get("name") if tag == "a" else None:
            self.ids.add(anchor_name)

        for attribute in LINK_ATTRIBUTES.get(tag, ()):
            if value := values.get(attribute):
                if attribute == "srcset":
                    self.links.extend(srcset_urls(value))
                else:
                    self.links.append(value.strip())

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def page_url(html_file: Path, public_dir: Path) -> str:
    relative = html_file.relative_to(public_dir).as_posix()
    if relative == "index.html":
        return f"{SITE_ORIGIN}/"
    if relative.endswith("/index.html"):
        return f"{SITE_ORIGIN}/{relative[:-10]}"
    return f"{SITE_ORIGIN}/{relative}"


def local_target(url: str, base_url: str, public_dir: Path) -> tuple[Path, str] | None:
    if not url:
        return None

    parsed = urlsplit(urljoin(base_url, url))
    if parsed.scheme in IGNORED_SCHEMES:
        return None
    if parsed.netloc and parsed.netloc != "sh1luo.github.io":
        return None

    path = unquote(parsed.path)
    if not path:
        return None
    return public_dir / path.lstrip("/"), unquote(parsed.fragment)


def resolved_file(target: Path) -> Path | None:
    if target.is_file():
        return target
    if (target / "index.html").is_file():
        return target / "index.html"
    html_target = target.with_suffix(".html")
    if html_target.is_file():
        return html_target
    return None


def parse_page(html_file: Path) -> PageParser:
    parser = PageParser()
    parser.feed(html_file.read_text(encoding="utf-8"))
    return parser


def main() -> int:
    public_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "public").resolve()
    if not public_dir.is_dir():
        print(f"Generated site directory does not exist: {public_dir}", file=sys.stderr)
        return 2

    pages = {html_file: parse_page(html_file) for html_file in sorted(public_dir.rglob("*.html"))}
    missing_targets: set[tuple[str, str]] = set()
    missing_fragments: set[tuple[str, str]] = set()

    for html_file, parser in pages.items():
        source = html_file.relative_to(public_dir).as_posix()
        base_url = page_url(html_file, public_dir)
        for link in parser.links:
            reference = local_target(link, base_url, public_dir)
            if reference is None:
                continue
            target, fragment = reference
            resolved = resolved_file(target)
            if resolved is None:
                missing_targets.add((source, link))
                continue
            if fragment and resolved.suffix == ".html":
                target_page = pages.get(resolved)
                if target_page is None:
                    target_page = parse_page(resolved)
                    pages[resolved] = target_page
                if fragment not in target_page.ids:
                    missing_fragments.add((source, link))

    for css_file in sorted(public_dir.rglob("*.css")):
        source = css_file.relative_to(public_dir).as_posix()
        base_url = f"{SITE_ORIGIN}/{source}"
        for link in CSS_URL_PATTERN.findall(css_file.read_text(encoding="utf-8")):
            reference = local_target(link.strip(), base_url, public_dir)
            if reference is None:
                continue
            target, _ = reference
            if resolved_file(target) is None:
                missing_targets.add((source, link.strip()))

    if missing_targets:
        print("Broken internal targets:", file=sys.stderr)
        for source, link in sorted(missing_targets):
            print(f"  {source}: {link}", file=sys.stderr)

    if missing_fragments:
        print("Broken internal fragments:", file=sys.stderr)
        for source, link in sorted(missing_fragments):
            print(f"  {source}: {link}", file=sys.stderr)

    if missing_targets or missing_fragments:
        return 1

    print("Internal target and fragment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
