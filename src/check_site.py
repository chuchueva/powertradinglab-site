#!/usr/bin/env python3
"""Checks on a built site: every local link resolves, no page over 200 KB,
no script tags. Usage: python3 src/check_site.py _site"""
import re
import sys
from pathlib import Path

LIMIT = 200 * 1024


def main(root):
    root = Path(root)
    errors = []
    for page in sorted(root.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        size = len(text.encode("utf-8"))
        if size > LIMIT:
            errors.append(f"{page}: {size} bytes, over 200 KB")
        if "<script" in text.lower():
            errors.append(f"{page}: contains a script tag")
        for url in re.findall(r'(?:href|src)="([^"]+)"', text):
            if re.match(r"[a-z]+:", url) or url.startswith("#"):
                continue
            path = url.split("#")[0].split("?")[0]
            target = (page.parent / path).resolve()
            if path.endswith("/") or path in ("", "./"):
                target = target / "index.html"
            if not target.exists():
                errors.append(f"{page.relative_to(root)}: broken link {url}")
    for e in errors:
        print(e, file=sys.stderr)
    print(f"{len(errors)} problem(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "_site")
