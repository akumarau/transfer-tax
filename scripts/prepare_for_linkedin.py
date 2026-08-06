"""
Prepare a markdown article for pasting into the LinkedIn article editor.

LinkedIn's editor does not accept markdown, and it has no table support at all.
This script produces two things:

  1. linkedin-article.html  - open in a browser, Ctrl+A, Ctrl+C, paste into
     LinkedIn. Headings, bold, italics, blockquotes and links all survive as
     rich text. Tables are removed and replaced with a visible marker telling
     you where to insert each image.

  2. table-1.png .. table-N.png - each table rendered as an image, because that
     is the only way to get a table into a LinkedIn article.

No third party packages. Uses headless Edge for the screenshots.

Usage:
    python prepare_for_linkedin.py <article.md> [output_dir]
"""

from __future__ import annotations

import html
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

# Matches LinkedIn's own article typography closely enough that the pasted
# result needs no cleanup.
PAGE_CSS = """
body { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
       max-width: 740px; margin: 40px auto; padding: 0 24px; color: #000000;
       font-size: 19px; line-height: 1.6; }
h1 { font-size: 40px; line-height: 1.2; margin: 0 0 8px; font-weight: 600; }
h2 { font-size: 26px; line-height: 1.3; margin: 40px 0 12px; font-weight: 600; }
h3 { font-size: 21px; line-height: 1.4; margin: 0 0 28px; font-weight: 400;
     color: #444444; }
p { margin: 0 0 20px; }
blockquote { margin: 24px 0; padding: 14px 20px; border-left: 3px solid #0a66c2;
             background: #f3f6f8; font-size: 20px; }
blockquote p { margin: 0; }
strong { font-weight: 600; }
hr { border: 0; border-top: 1px solid #e0e0e0; margin: 36px 0; }
em { font-style: italic; }
.imgmark { background: #fff3cd; border: 2px dashed #d39e00; padding: 14px 18px;
           margin: 24px 0; font-family: Consolas, monospace; font-size: 15px;
           color: #665100; }
"""

TABLE_CSS = """
body { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
       margin: 0; padding: 24px; background: #ffffff; }
table { border-collapse: collapse; font-size: 26px; width: 100%; }
th { background: #0a66c2; color: #ffffff; text-align: left; padding: 16px 20px;
     font-weight: 600; white-space: nowrap; }
td { padding: 14px 20px; border-bottom: 1px solid #e3e3e3; white-space: nowrap; }
tr:nth-child(even) td { background: #f6f8fa; }
td.num, th.num { text-align: right; }
strong { font-weight: 700; color: #0a66c2; }
"""


def find_edge() -> str | None:
    for path in EDGE_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def inline(text: str) -> str:
    """Bold, italics and links. Escapes HTML first so content cannot inject."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\\\*", "\x00STAR\x00", text)          # protect \*
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text.replace("\x00STAR\x00", "*")


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse(md: str):
    """Returns (blocks, tables). Blocks are ('type', payload) tuples."""
    lines = md.split("\n")
    blocks: list[tuple[str, object]] = []
    tables: list[dict] = []
    buf: list[str] = []
    i = 0

    def flush() -> None:
        if buf:
            blocks.append(("p", " ".join(buf).strip()))
            buf.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush()
            i += 1
            continue

        if stripped.startswith("#"):
            flush()
            level = len(stripped) - len(stripped.lstrip("#"))
            blocks.append((f"h{min(level, 3)}", stripped.lstrip("#").strip()))
            i += 1
            continue

        if re.fullmatch(r"-{3,}", stripped):
            flush()
            blocks.append(("hr", ""))
            i += 1
            continue

        if stripped.startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                piece = lines[i].strip().lstrip(">").strip()
                if piece:
                    quote.append(piece)
                i += 1
            blocks.append(("quote", " ".join(quote)))
            continue

        # A table needs a header row followed by a |---|---| separator.
        if (stripped.startswith("|")
                and i + 1 < len(lines)
                and re.fullmatch(r"\|[\s:\-|]+\|", lines[i + 1].strip())):
            flush()
            header = split_row(lines[i])
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            tables.append({"header": header, "rows": rows})
            blocks.append(("table", len(tables)))
            continue

        buf.append(stripped)
        i += 1

    flush()
    return blocks, tables


def render_article(blocks) -> str:
    out = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>Paste this into LinkedIn</title>",
        f"<style>{PAGE_CSS}</style></head><body>",
        "<div class='imgmark'>HOW TO USE: select everything below this box "
        "(Ctrl+A then Ctrl+C) and paste into the LinkedIn article editor. "
        "Delete this box after pasting. Where you see a yellow TABLE marker, "
        "upload the matching table-N.png instead.</div>",
    ]
    for kind, payload in blocks:
        if kind == "table":
            out.append(
                f"<div class='imgmark'>&#9660; INSERT IMAGE table-{payload}.png HERE "
                f"&#9660;</div>")
        elif kind == "hr":
            out.append("<hr>")
        elif kind == "quote":
            out.append(f"<blockquote><p>{inline(str(payload))}</p></blockquote>")
        elif kind.startswith("h"):
            out.append(f"<{kind}>{inline(str(payload))}</{kind}>")
        else:
            out.append(f"<p>{inline(str(payload))}</p>")
    out.append("</body></html>")
    return "\n".join(out)


def render_table(tbl: dict) -> str:
    def numeric(cell: str) -> bool:
        return bool(re.match(r"^[\*\s]*[\d.α<>~+-]", cell)) and any(
            ch.isdigit() for ch in cell)

    head = "".join(
        f"<th class='{'num' if idx else ''}'>{inline(c)}</th>"
        for idx, c in enumerate(tbl["header"]))
    body = ""
    for row in tbl["rows"]:
        cells = "".join(
            f"<td class='{'num' if idx and numeric(c) else ''}'>{inline(c)}</td>"
            for idx, c in enumerate(row))
        body += f"<tr>{cells}</tr>"
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{TABLE_CSS}</style></head><body>"
            f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
            f"</body></html>")


def shoot(edge: str, html_path: Path, png_path: Path, rows: int, cols: int,
          profile: Path) -> bool:
    width = min(1800, 560 + cols * 300)
    height = 110 + rows * 62
    if png_path.exists():
        png_path.unlink()
    cmd = [
        edge, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--no-first-run", "--no-default-browser-check",
        f"--user-data-dir={profile}",
        "--force-device-scale-factor=2", f"--window-size={width},{height}",
        f"--screenshot={png_path}", html_path.as_uri(),
    ]
    for _ in range(3):
        subprocess.run(cmd, capture_output=True, timeout=120)
        time.sleep(1.0)
        if png_path.exists() and png_path.stat().st_size > 0:
            return True
        time.sleep(1.5)
    return False


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    src = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else src.parent / "linkedin"
    out_dir.mkdir(parents=True, exist_ok=True)

    blocks, tables = parse(src.read_text(encoding="utf-8"))

    article = out_dir / "linkedin-article.html"
    article.write_text(render_article(blocks), encoding="utf-8")
    print(f"[ok]  article  -> {article}")

    edge = find_edge()
    if not edge:
        print("[warn] Edge not found; skipping table images.")
        return

    profile = Path(tempfile.gettempdir()) / "edge_linkedin_shots"
    sources = []
    # Each table gets its own source file. Sharing one temp file lets a slow
    # Edge process screenshot the next table's markup.
    for n, tbl in enumerate(tables, start=1):
        src_html = out_dir / f"_table-{n}.html"
        src_html.write_text(render_table(tbl), encoding="utf-8")
        sources.append(src_html)

    for n, (tbl, src_html) in enumerate(zip(tables, sources), start=1):
        png = out_dir / f"table-{n}.png"
        ok = shoot(edge, src_html, png, len(tbl["rows"]) + 1, len(tbl["header"]),
                   profile)
        label = tbl["header"][0][:38].encode("ascii", "replace").decode()
        size = f"{png.stat().st_size // 1024} KB" if ok else "FAILED"
        print(f"[{'ok' if ok else '!!'}]  table {n}  -> {png.name}  ({size})  [{label}]")

    time.sleep(2)
    for src_html in sources:
        src_html.unlink(missing_ok=True)

    print(f"\n{len(tables)} tables rendered. Open {article.name} in a browser, "
          f"select all, copy, paste into LinkedIn.")


if __name__ == "__main__":
    main()
