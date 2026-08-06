"""
Generate cover images for the Transfer Tax article.

Renders SVG through headless Edge, so there are no third party packages and no
image generation service involved. Every number drawn comes from the model in
transfer_tax/, so the picture cannot drift away from the article.

Usage:
    python scripts/make_cover_image.py [output_dir]
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transfer_tax import CaseParams, labour_minutes, retained_context  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

BASE = CaseParams()
INK = "#0A1F33"
BLUE = "#2E8FE0"
BLUE_DIM = "#1B5C96"
AMBER = "#FF9E2C"
PAPER = "#F2F6FA"
MUTED = "#8FA8BF"


def find_edge() -> str | None:
    for path in EDGE_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def shoot(edge: str, html_path: Path, png: Path, w: int, h: int) -> bool:
    if png.exists():
        png.unlink()
    profile = Path(tempfile.gettempdir()) / "edge_cover_shots"
    cmd = [
        edge, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--no-first-run", "--no-default-browser-check",
        f"--user-data-dir={profile}", "--force-device-scale-factor=2",
        f"--window-size={w},{h}", f"--screenshot={png}", html_path.as_uri(),
    ]
    for _ in range(3):
        subprocess.run(cmd, capture_output=True, timeout=120)
        time.sleep(1.0)
        if png.exists() and png.stat().st_size > 0:
            return True
        time.sleep(1.5)
    return False


def series(max_n: int = 4):
    """The article's own numbers, pulled straight from the model."""
    return [
        {
            "n": n,
            "context": retained_context(BASE.rho, n),
            "labour": labour_minutes(n, BASE),
        }
        for n in range(max_n + 1)
    ]


def wrap(svg: str, w: int, h: int) -> str:
    return (
        "<!doctype html><html><head><meta charset='utf-8'><style>"
        "html,body{margin:0;padding:0;background:#0A1F33;}"
        "svg{display:block;}</style></head><body>" + svg + "</body></html>"
    )


def defs() -> str:
    return f"""
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#0B2439"/>
        <stop offset="55%" stop-color="#0A1F33"/>
        <stop offset="100%" stop-color="#071726"/>
      </linearGradient>
      <linearGradient id="bar" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="{BLUE}"/>
        <stop offset="100%" stop-color="{BLUE_DIM}"/>
      </linearGradient>
      <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="{AMBER}" stop-opacity="0.15"/>
        <stop offset="100%" stop-color="{AMBER}" stop-opacity="0.75"/>
      </linearGradient>
      <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
        <feGaussianBlur stdDeviation="7" result="b"/>
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>
    """


def chart(x0: int, y0: int, x1: int, y1: int, data, label_size: int = 17) -> str:
    """Bars = context surviving. Line = labour cost. They cross. That is the story."""
    n = len(data)
    span = (x1 - x0) / n
    centres = [x0 + span * (i + 0.5) for i in range(n)]
    bar_w = min(58, span * 0.42)
    base_y = y1
    max_bar = y1 - y0 - 40

    lab = [d["labour"] for d in data]
    lo, hi = min(lab), max(lab)

    def cost_y(v: float) -> float:
        return base_y - (v - lo) / (hi - lo) * max_bar

    parts = []

    # baseline
    parts.append(
        f'<line x1="{x0 - 10}" y1="{base_y}" x2="{x1 + 10}" y2="{base_y}" '
        f'stroke="{MUTED}" stroke-opacity="0.35" stroke-width="2"/>')

    pts = [(c, cost_y(d["labour"])) for c, d in zip(centres, data)]

    # Cost area goes down FIRST so the context bars stay crisp on top of it.
    area = (f'{pts[0][0]:.1f},{base_y} ' +
            " ".join(f"{px:.1f},{py:.1f}" for px, py in pts) +
            f' {pts[-1][0]:.1f},{base_y}')
    parts.append(f'<polygon points="{area}" fill="url(#fade)" opacity="0.55"/>')

    # context bars
    for c, d in zip(centres, data):
        h = d["context"] * max_bar
        parts.append(
            f'<rect x="{c - bar_w / 2:.1f}" y="{base_y - h:.1f}" width="{bar_w:.1f}" '
            f'height="{h:.1f}" rx="5" fill="url(#bar)"/>')

    # cost line on top of the bars
    parts.append(
        '<polyline points="' +
        " ".join(f"{px:.1f},{py:.1f}" for px, py in pts) +
        f'" fill="none" stroke="{AMBER}" stroke-width="4.5" '
        f'stroke-linejoin="round" stroke-linecap="round" filter="url(#glow)"/>')

    # context labels, sitting just above each bar
    for c, d in zip(centres, data):
        h = d["context"] * max_bar
        parts.append(
            f'<text x="{c:.1f}" y="{base_y - h - 14:.1f}" fill="{PAPER}" '
            f'font-size="{label_size}" font-weight="700" text-anchor="middle">'
            f'{d["context"] * 100:.0f}%</text>')

    for (px, py), d in zip(pts, data):
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7" fill="#0A1F33" '
                     f'stroke="{AMBER}" stroke-width="4"/>')
        parts.append(
            f'<text x="{px:.1f}" y="{py - 20:.1f}" fill="{AMBER}" '
            f'font-size="{label_size}" font-weight="700" text-anchor="middle">'
            f'{d["labour"]:.0f}m</text>')

    # x axis labels
    for c, d in zip(centres, data):
        parts.append(
            f'<text x="{c:.1f}" y="{base_y + 30:.1f}" fill="{MUTED}" '
            f'font-size="{label_size}" text-anchor="middle">{d["n"]}</text>')

    # legend
    parts.append(
        f'<rect x="{x0}" y="{y0 - 6}" width="13" height="13" rx="3" fill="{BLUE}"/>'
        f'<text x="{x0 + 21}" y="{y0 + 5}" fill="{MUTED}" font-size="{label_size - 2}">'
        f'context surviving</text>'
        f'<line x1="{x0 + 178}" y1="{y0 + 1}" x2="{x0 + 208}" y2="{y0 + 1}" '
        f'stroke="{AMBER}" stroke-width="4" stroke-linecap="round"/>'
        f'<text x="{x0 + 216}" y="{y0 + 5}" fill="{MUTED}" font-size="{label_size - 2}">'
        f'labour cost</text>')

    return "".join(parts)


def cover_wide(data) -> str:
    W, H = 1200, 628
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" font-family="Segoe UI, Helvetica, Arial, sans-serif">',
           defs(), f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']

    svg.append(f'<rect x="0" y="0" width="7" height="{H}" fill="{AMBER}"/>')
    svg.append(f'<text x="58" y="92" fill="{MUTED}" font-size="16" letter-spacing="3.5" '
               f'font-weight="600">SUPPORT OPERATIONS</text>')
    svg.append(f'<text x="56" y="176" fill="{PAPER}" font-size="70" '
               f'font-weight="700" letter-spacing="-1.5">The Transfer Tax</text>')
    svg.append(f'<text x="58" y="228" fill="{BLUE}" font-size="26" font-weight="500">'
               f'What every handoff really costs</text>')

    svg.append(f'<line x1="58" y1="270" x2="440" y2="270" stroke="{MUTED}" '
               f'stroke-opacity="0.28" stroke-width="1.5"/>')

    facts = [
        ("2.1", "\u00d7", "the labour cost after three transfers"),
        ("18", "\u00d7", "the elapsed time the customer waits"),
        ("42", "%", "of the original context still surviving"),
    ]
    y = 322
    for big, unit, text in facts:
        svg.append(f'<text x="58" y="{y}" fill="{AMBER}" font-size="42" '
                   f'font-weight="700">{big}<tspan font-size="26">{unit}</tspan></text>')
        svg.append(f'<text x="152" y="{y - 4}" fill="{PAPER}" font-size="18" '
                   f'opacity="0.92">{text}</text>')
        y += 74

    svg.append(f'<text x="58" y="{H - 42}" fill="{MUTED}" font-size="16">'
               f'github.com/akumarau/transfer-tax</text>')

    svg.append(f'<text x="612" y="92" fill="{MUTED}" font-size="15" letter-spacing="2">'
               f'CONTEXT SURVIVING vs LABOUR COST</text>')
    svg.append(chart(612, 120, 1150, 520, data))
    svg.append(f'<text x="881" y="{H - 42}" fill="{MUTED}" font-size="15" '
               f'text-anchor="middle">NUMBER OF TRANSFERS</text>')

    svg.append("</svg>")
    return wrap("".join(svg), W, H), W, H


def cover_square(data) -> str:
    W, H = 1080, 1080
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" font-family="Segoe UI, Helvetica, Arial, sans-serif">',
           defs(), f'<rect width="{W}" height="{H}" fill="url(#bg)"/>']

    svg.append(f'<rect x="0" y="0" width="{W}" height="9" fill="{AMBER}"/>')
    svg.append(f'<text x="72" y="140" fill="{MUTED}" font-size="19" letter-spacing="4" '
               f'font-weight="600">SUPPORT OPERATIONS</text>')
    svg.append(f'<text x="70" y="232" fill="{PAPER}" font-size="82" font-weight="700" '
               f'letter-spacing="-2">The Transfer Tax</text>')
    svg.append(f'<text x="72" y="288" fill="{BLUE}" font-size="30">'
               f'What every handoff really costs</text>')

    svg.append(f'<text x="72" y="392" fill="{MUTED}" font-size="17" letter-spacing="2">'
               f'CONTEXT SURVIVING vs LABOUR COST</text>')
    svg.append(chart(90, 420, 1000, 800, data, label_size=19))
    svg.append(f'<text x="545" y="872" fill="{MUTED}" font-size="17" '
               f'text-anchor="middle">NUMBER OF TRANSFERS</text>')

    svg.append(f'<line x1="72" y1="922" x2="1008" y2="922" stroke="{MUTED}" '
               f'stroke-opacity="0.25" stroke-width="1.5"/>')
    svg.append(f'<text x="72" y="984" fill="{PAPER}" font-size="27" font-weight="600">'
               f'Three transfers. Double the cost. Eighteen times the wait.</text>')
    svg.append(f'<text x="72" y="1026" fill="{MUTED}" font-size="19">'
               f'github.com/akumarau/transfer-tax</text>')

    svg.append("</svg>")
    return wrap("".join(svg), W, H), W, H


def main() -> None:
    out = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd() / "cover"
    out.mkdir(parents=True, exist_ok=True)

    edge = find_edge()
    if not edge:
        print("[!!] Edge not found.")
        sys.exit(1)

    data = series()
    print("Numbers taken from the model:")
    for d in data:
        print(f"  {d['n']} transfers  context {d['context']:6.1%}  "
              f"labour {d['labour']:6.1f} min")
    print()

    for name, builder in (("cover-wide", cover_wide), ("cover-square", cover_square)):
        html, w, h = builder(data)
        src = out / f"_{name}.html"
        src.write_text(html, encoding="utf-8")
        png = out / f"{name}.png"
        ok = shoot(edge, src, png, w, h)
        size = f"{png.stat().st_size // 1024} KB" if ok else "FAILED"
        print(f"[{'ok' if ok else '!!'}]  {png.name}  {w}x{h}  ({size})")

    time.sleep(1)
    for f in out.glob("_*.html"):
        f.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
