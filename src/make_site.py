#!/usr/bin/env python3
"""Build the PowerTradingLab site.

Reads data/v1/* and data/status.xml (heartbeat and version only), plus the
hand-written pages in content/. Writes plain HTML into --out. Standard library
only, no JavaScript, deterministic: the same inputs give byte-identical output.

    python3 src/make_site.py --out _site
"""
import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONTENT = ROOT / "content"
SRC = ROOT / "src"

SITE_URL = "https://powertradinglab.org"
DATA_PATH = "benchmarks/data/"          # where data/ is mirrored on the site
EMAIL = "chuchueva@powertradinglab.org"
GITHUB = "https://github.com/chuchueva"
DESCRIPTION = "Irina Chuchueva's Open Research Platform: European Power Trading Benchmarks"
NOT_COPIED = {"og.svg", "og.png"}   # everything else in src/img goes to /img; og.png goes to the root

VALUES = [
    ("extractable_value", "Extractable"),
    ("trailing_bias_value", "Trailing bias"),
    ("passive_da_buy_value", "Passive DA buy"),
    ("passive_da_sell_value", "Passive DA sell"),
    ("adverse_value", "Adverse"),
]
UNIT = "EUR per 1 MW of trading capacity, summed over the delivery day"

NAV = [
    ("benchmarks/", "Benchmarks"),
    ("docs/", "Docs"),
    ("news/", "News"),
    ("about/", "About"),
    ("support/", "Support"),
    ("contact/", "Contact"),
]


class BuildError(Exception):
    pass


# ---------------------------------------------------------------- reading

def esc(s):
    return html.escape(str(s), quote=True)


def read_csv(name):
    path = DATA / "v1" / name
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_status():
    root = ET.parse(DATA / "status.xml").getroot()
    ver = root.find("version")
    areas = {}
    for a in root.findall("area"):
        src = a.find("source")
        areas[a.get("code")] = dict(src.attrib) if src is not None else {}
    return {
        "generated_ts": root.findtext("generated_ts") or "",
        "schema": ver.get("schema"),
        "methodology": ver.get("methodology"),
        "areas": areas,
    }


def verify_files(index):
    """The server pushes data/ as one unit; a half-pushed set must not build."""
    for f in index["files"]:
        path = DATA / "v1" / f["name"]
        if not path.exists():
            raise BuildError(f"index.json lists {f['name']}, which is missing")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != f["sha256"]:
            raise BuildError(f"sha256 of {f['name']} does not match index.json")


# ---------------------------------------------------------------- formatting

def num(x):
    return f"{float(x):,.2f}".replace("-", "−")


def ts(x):
    return f"{x[:10]} {x[11:16]} UTC" if x else "not stated"


def full_ptu(tzname, day):
    tz = ZoneInfo(tzname)
    d = date.fromisoformat(day)
    n = d + timedelta(days=1)
    a = datetime(d.year, d.month, d.day, tzinfo=tz).astimezone(timezone.utc)
    b = datetime(n.year, n.month, n.day, tzinfo=tz).astimezone(timezone.utc)
    return int((b - a).total_seconds() // 900)


def reason_text(code):
    parts = code.split(":")
    kind = parts[0]
    day = parts[1] if len(parts) > 1 else ""
    leg = f" ({parts[2]} leg)" if len(parts) > 2 and parts[2] else ""
    known = {
        "input_incomplete": f"the input for {day}{leg} was incomplete",
        "hour_incomplete": f"some hours of the input for {day}{leg} were incomplete",
    }
    text = known.get(kind, "of reason code")
    return f"{text} (<code>{esc(code)}</code>)"


def forecast_statement(r):
    ptu, n = int(r["ptu"]), int(r["ptu_no_action"])
    why = r.get("skip_reason", "")
    if n == 0:
        return f"Decided on all {ptu} PTU."
    if why and n == ptu:
        return f"Forecast declined: no decision on any of the {ptu} PTU because {reason_text(why)}."
    if why:
        return f"Partly declined: {n} of {ptu} PTU without a decision because {reason_text(why)}."
    if n == ptu:
        return f"The signal did not form on any of the {ptu} PTU; nothing was refused."
    return f"The signal did not form on {n} of {ptu} PTU; nothing was refused."


def score_statements(r, tzname):
    out = []
    ptu = int(r["ptu"])
    pwa = int(r["ptu_with_action"] or 0)
    full = full_ptu(tzname, r["delivery_day"])
    if ptu < full:
        out.append(f"The source published {ptu} of {full} PTU; the day is graded on the {ptu} that exist.")
    if pwa == 0:
        out.append("No decision was issued for this day, so there is no trailing-bias result. "
                   "The four market values are graded regardless.")
    elif pwa < ptu:
        out.append(f"A decision covered {pwa} of {ptu} PTU; trailing bias is a sum over those {pwa}.")
    return out


# ---------------------------------------------------------------- markdown

def md(text, rel):
    """A small markdown subset: # headings, paragraphs, - lists, ``` blocks,
    `code`, **bold**, *italic*, [text](url), ![alt](url){width=N}, and
    blocks "::: name" ... ":::" -> <div class="name">. "::: side" whose first
    line is an image puts the image left and the rest to its right. A url starting with / is made
    relative, so the pages work under any base path."""

    def inline(s):
        s = esc(s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<em>\1</em>", s)

        def image(m):
            url = m.group(2)
            if url.startswith("/"):
                url = rel(url[1:])
            width = f' width="{m.group(3)}"' if m.group(3) else ""
            return f'<img src="{url}" alt="{m.group(1)}"{width}>'
        s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)(?:\{width=(\d+)\})?", image, s)

        def link(m):
            url = m.group(2)
            if url.startswith("/"):
                url = rel(url[1:])
            return f'<a href="{url}">{m.group(1)}</a>'
        return re.sub(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)", link, s)

    blocks = []

    def block(m):
        name, inner = m.group(1), m.group(2)
        lines = inner.strip("\n").splitlines()
        if name == "side" and lines and lines[0].startswith("!["):
            body = (f'<div class="side"><div class="side-media">{md(lines[0], rel)}</div>'
                    f'<div class="side-text">{md(chr(10).join(lines[1:]), rel)}</div></div>')
        else:
            body = f'<div class="{esc(name)}">{md(inner, rel)}</div>'
        blocks.append(body)
        return f"\x00{len(blocks) - 1}\x00"

    text = re.sub(r"^:::\s*([\w-]+)\s*\n(.*?)\n:::\s*$", block, text, flags=re.S | re.M)

    out, para, items, code = [], [], [], None

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for line in text.splitlines():
        if code is not None:
            if line.startswith("```"):
                out.append("<pre><code>" + esc("\n".join(code)) + "</code></pre>")
                code = None
            else:
                code.append(line)
            continue
        if m := re.fullmatch(r"\x00(\d+)\x00", line.strip()):
            flush()
            out.append(blocks[int(m.group(1))])
        elif line.startswith("```"):
            flush()
            code = []
        elif not line.strip():
            flush()
        elif m := re.match(r"(#{1,4})\s+(.*)", line):
            flush()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
        elif line.startswith("- "):
            if para:
                flush()
            items.append(line[2:])
        elif items and line.startswith("  "):
            items[-1] += " " + line.strip()
        else:
            if items:
                flush()
            para.append(line.strip())
    flush()
    return "\n".join(out)


def content(name):
    path = CONTENT / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


# ---------------------------------------------------------------- news

def read_news():
    entries, cur = [], None
    for line in content("news.md").splitlines():
        m = re.match(r"##\s+(\d{4}-\d{2}-\d{2})\s*$", line)
        if m:
            cur = {"date": m.group(1), "versions": {}, "lines": []}
            entries.append(cur)
        elif cur is not None and line.lower().startswith("versions:"):
            for k, v in re.findall(r"(schema|methodology)\s+(\d+)", line.lower()):
                cur["versions"][k] = v
        elif cur is not None:
            cur["lines"].append(line)
    # newest first; same date keeps file order
    order = sorted(range(len(entries)), key=lambda i: (entries[i]["date"], -i), reverse=True)
    return [entries[i] for i in order]


def check_versions(news, status):
    announced = {"schema": set(), "methodology": set()}
    for e in news:
        for k, v in e["versions"].items():
            announced[k].add(v)
    missing = [f"{k} {status[k]}" for k in ("schema", "methodology")
               if status[k] not in announced[k]]
    if missing:
        raise BuildError(
            "status.xml declares " + " and ".join(missing) +
            ", but no entry in content/news.md announces it. Add an entry with a line "
            f"'versions: schema {status['schema']}, methodology {status['methodology']}'.")


# ---------------------------------------------------------------- layout

class Ctx:
    pass


def layout(ctx, path, title, body):
    depth = path.count("/")

    def rel(target):
        return ("../" * depth + target) or "./"

    current = ' aria-current="page"'
    nav = "".join(
        f'<a href="{rel(u)}"{current if path == u else ""}>{n}</a>' for u, n in NAV)
    full_title = f"{title} — PowerTradingLab" if title else "PowerTradingLab"
    st = ctx.status
    footer = (
        f'<p>Schema {esc(st["schema"])} · Methodology {esc(st["methodology"])} · '
        f'Data through {ts(ctx.index["generated_from"])} · Last run {ts(st["generated_ts"])}</p>'
        '<p>Derived from data published on the ENTSO-E Transparency Platform; imbalance prices '
        'reused under CC-BY 4.0. No day-ahead or imbalance prices are republished.</p>'
        f'<p><a href="mailto:{EMAIL}">{EMAIL}</a> · <a href="{GITHUB}">GitHub</a> · '
        f'<a href="{rel("chuchueva/")}">Irina Chuchueva</a></p>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(DESCRIPTION)}">
<link rel="canonical" href="{SITE_URL}/{path}">
<link rel="icon" href="{rel('img/mark.svg')}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{rel('img/apple-touch-icon.png')}">
<meta property="og:image" content="{SITE_URL}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(DESCRIPTION)}">
<meta property="og:url" content="{SITE_URL}/{path}">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{rel('style.css')}">
</head>
<body>
<header><div class="wrap"><a class="brand" href="{rel('')}"><img src="{rel('img/logo.svg')}" alt="PowerTradingLab" width="584" height="88"></a><nav>{nav}</nav></div></header>
<main class="wrap">
{body(rel)}
</main>
<footer><div class="wrap">{footer}</div></footer>
</body>
</html>
"""


def data_link(rel, source_file, label):
    return f'<a href="{rel(DATA_PATH + source_file)}">{label}</a>'


# ---------------------------------------------------------------- tables

def not_comparable(r, colspan=1):
    return (f'<td class="muted" colspan="{colspan}">Methodology {esc(r["methodology_version"])}: '
            'not comparable, not shown</td>')


def value_cells(r):
    cells = []
    for key, _ in VALUES:
        v = r[key]
        if v == "":
            cells.append('<td class="muted">no decision</td>')
        else:
            cells.append(f'<td class="n">{num(v)}</td>')
    return "".join(cells)


def latest_scores_table(ctx, rel):
    head = "".join(f"<th>{lbl}</th>" for _, lbl in VALUES)
    rows, notes = [], []
    for z in ctx.zone_codes:
        r = ctx.latest_score.get(z)
        if r is None:
            rows.append(f'<tr><th><a href="{rel("benchmarks/")}#{z}">{z}</a></th>'
                        f'<td colspan="9" class="muted">No graded day published yet.</td></tr>')
            continue
        if r["methodology_version"] != ctx.m:
            cells = f'<td>{r["delivery_day"]}</td>' + not_comparable(r, 8)
        else:
            cells = (f'<td>{r["delivery_day"]}</td><td class="nw">{esc(r["pass"])}</td>' + value_cells(r) +
                     f'<td class="n">{r["ptu"]} / {r["ptu_with_action"]}</td>'
                     f'<td>{data_link(rel, r["source_file"], "score")}</td>')
            for s in score_statements(r, ctx.zones[z]["timezone"]):
                notes.append(f"<li><strong>{z} {r['delivery_day']}.</strong> {s}</li>")
        rows.append(f'<tr><th><a href="{rel("benchmarks/")}#{z}">{z}</a></th>{cells}</tr>')
    note_html = f'<ul class="notes">{"".join(notes)}</ul>' if notes else ""
    return (f'<div class="scroll"><table><caption>{UNIT}.</caption>'
            f'<thead><tr><th>Zone</th><th>Delivery day</th><th>Pass</th>{head}'
            f'<th>PTU graded / decided</th><th>File</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>{note_html}')


def latest_forecasts_table(ctx, rel):
    rows = []
    for z in ctx.zone_codes:
        r = ctx.latest_forecast.get(z)
        if r is None:
            rows.append(f'<tr><th>{z}</th><td colspan="6" class="muted">No forecast published yet.</td></tr>')
            continue
        if r["methodology_version"] != ctx.m:
            rows.append(f'<tr><th>{z}</th><td>{r["delivery_day"]}</td>{not_comparable(r, 5)}</tr>')
            continue
        rows.append(
            f'<tr><th>{z}</th><td>{r["delivery_day"]}</td>'
            f'<td class="n">{r["ptu_buy"]}</td><td class="n">{r["ptu_sell"]}</td>'
            f'<td class="n">{r["ptu_no_action"]}</td><td>{ts(r["knownby_ts"])}</td>'
            f'<td>{data_link(rel, r["source_file"], "forecast")}</td></tr>'
            f'<tr class="sub"><td></td><td colspan="6">{forecast_statement(r)}</td></tr>')
    return ('<div class="scroll"><table><caption>The decision is counted in PTU: buy on the day-ahead '
            'auction, sell, or no action. Each was published before the auction gate.</caption>'
            '<thead><tr><th>Zone</th><th>Delivery day</th><th>Buy</th><th>Sell</th>'
            '<th>No action</th><th>Published</th><th>File</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def method_note(ctx, rows, what):
    old = [r for r in rows if r["methodology_version"] != ctx.m]
    if not old:
        return ""
    cur = [r for r in rows if r["methodology_version"] == ctx.m]
    olds = ", ".join(sorted({r["methodology_version"] for r in old}))
    since = f" since {min(r['delivery_day'] for r in cur)}" if cur else ""
    span = f"{min(r['delivery_day'] for r in old)} to {max(r['delivery_day'] for r in old)}"
    return (f'<p class="note">{what}: methodology {ctx.m}{since}. Days {span} were computed under '
            f'methodology {olds} and are not comparable; they stay in the CSV files. '
            f'See <a href="NEWS">News</a>.</p>')


def zone_days_table(ctx, z, rel):
    tzname = ctx.zones[z]["timezone"]
    scores = {r["delivery_day"]: r for r in ctx.scores[z]}
    fcs = {r["delivery_day"]: r for r in ctx.forecasts[z]}
    cur_scores = sorted(d for d, r in scores.items() if r["methodology_version"] == ctx.m)
    cur_fcs = sorted(d for d, r in fcs.items() if r["methodology_version"] == ctx.m)
    if not cur_scores and not cur_fcs:
        return '<p class="muted">No delivery day under the current methodology yet.</p>'
    last_score = cur_scores[-1] if cur_scores else None
    end = max(([last_score] if last_score else []) + ([cur_fcs[-1]] if cur_fcs else []))
    first_cur = min(cur_scores + cur_fcs)
    start = date.fromisoformat(last_score or end) - timedelta(days=2)
    start = max(start, date.fromisoformat(first_cur))
    days = []
    d = date.fromisoformat(end)
    while d >= start:
        days.append(d.isoformat())
        d -= timedelta(days=1)

    head = "".join(f"<th>{lbl}</th>" for _, lbl in VALUES)
    rows = []
    for day in days:
        notes, files = [], []
        f = fcs.get(day)
        if f is None:
            fcell = '<td class="muted">none</td>'
            notes.append("No forecast was published for this day.")
        elif f["methodology_version"] != ctx.m:
            fcell = not_comparable(f)
            files.append(data_link(rel, f["source_file"], "forecast"))
        else:
            fcell = (f'<td class="n">{f["ptu_buy"]} / {f["ptu_sell"]} / {f["ptu_no_action"]}</td>')
            notes.append(forecast_statement(f))
            files.append(data_link(rel, f["source_file"], "forecast"))
        s = scores.get(day)
        if s is None:
            if last_score is None or day > last_score:
                scell = '<td colspan="6" class="muted">Not graded yet.</td>'
            else:
                scell = '<td colspan="6" class="muted">Not graded: no score was published for this day.</td>'
        elif s["methodology_version"] != ctx.m:
            scell = not_comparable(s, 6)
            files.append(data_link(rel, s["source_file"], "score"))
        else:
            scell = value_cells(s) + f'<td class="n">{s["ptu"]} / {s["ptu_with_action"]}</td>'
            notes.extend(score_statements(s, tzname))
            notes.append(f"Pass: {esc(s['pass'])}.")
            files.append(data_link(rel, s["source_file"], "score"))
        rows.append(f'<tr><th>{day}</th>{fcell}{scell}</tr>'
                    f'<tr class="sub"><td></td><td colspan="7">{" ".join(notes)} '
                    f'{" · ".join(files)}</td></tr>')
    return (f'<div class="scroll"><table><caption>Newest days first. Decision: PTU buy / sell / '
            f'no action. Values: {UNIT}.</caption>'
            f'<thead><tr><th>Delivery day</th><th>Decision</th>{head}'
            f'<th>PTU graded / decided</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def downloads(ctx, z, rel):
    sizes = {f["name"]: f["bytes"] for f in ctx.index["files"]}
    items = []
    for kind in ("scores", "forecasts"):
        for suffix, what in (("", "full history"), ("-90d", "last 90 days"), ("-latest", "latest day")):
            name = f"{z}_{kind}{suffix}.csv"
            if name in sizes:
                items.append(f'<li>{data_link(rel, "v1/" + name, name)} — {kind}, {what}, '
                             f'{sizes[name]:,} bytes</li>')
    return f'<ul class="files">{"".join(items)}</ul>'


def definitions(ctx):
    b = ctx.index["benchmarks"]
    return "<dl>" + "".join(
        f"<dt>{lbl} <code>{key}</code></dt><dd>{esc(b.get(key, ''))}</dd>" for key, lbl in VALUES
    ) + "</dl>"


# ---------------------------------------------------------------- pages

def page_home(ctx):
    def body(rel):
        st = ctx.status
        through = ", ".join(
            f"{z} {ts(st['areas'].get(z, {}).get('im_through', ''))}" for z in ctx.zone_codes)
        b = ctx.index["benchmarks"]
        return f"""{md(content('home.md'), rel)}
<p class="fresh">Last run {ts(st['generated_ts'])}. Imbalance data through: {through}.</p>
<h2>Latest graded day</h2>
{latest_scores_table(ctx, rel)}
<h2>Next decision</h2>
{latest_forecasts_table(ctx, rel)}
<h2>Two things measured</h2>
<dl>
<dt>How fat a market is: <code>extractable_value</code></dt><dd>{esc(b.get('extractable_value', ''))}</dd>
<dt>How much a mechanical rule takes: <code>trailing_bias_value</code></dt><dd>{esc(b.get('trailing_bias_value', ''))}</dd>
</dl>
<p><a href="{rel('benchmarks/')}">All zones</a> · <a href="{rel('docs/data/')}">The data</a> · <a href="{rel('docs/')}">The report and the methodology</a></p>"""
    return layout(ctx, "", "", body)


def page_benchmarks(ctx):
    def body(rel):
        st = ctx.status
        srows = "".join(
            f"<tr><th>{z}</th><td>{ts(st['areas'].get(z, {}).get('da_through', ''))}</td>"
            f"<td>{ts(st['areas'].get(z, {}).get('im_through', ''))}</td>"
            f"<td>{ts(st['areas'].get(z, {}).get('last_poll', ''))}</td></tr>"
            for z in ctx.zone_codes)
        zone_blocks = []
        for z in ctx.zone_codes:
            zi = ctx.zones[z]
            meta = (f"EIC <code>{esc(zi.get('eic', ''))}</code> · {esc(zi.get('timezone', ''))} · "
                    f"day-ahead in {esc(zi.get('day_ahead_currency', ''))}, imbalance in "
                    f"{esc(zi.get('imbalance_currency', ''))} · delivery days published "
                    f"{esc(zi.get('first_delivery_day', ''))} to {esc(zi.get('last_delivery_day', ''))}")
            notes = (method_note(ctx, ctx.scores[z], "Scores") +
                     method_note(ctx, ctx.forecasts[z], "Forecasts")).replace("NEWS", rel("news/"))
            zone_blocks.append(
                f'<section id="{z}"><h2>{z}</h2><p class="meta">{meta}</p>{notes}'
                f'{zone_days_table(ctx, z, rel)}<h3>Download</h3>{downloads(ctx, z, rel)}</section>')
        return f"""<h1>Benchmarks</h1>
<p class="version">Schema {esc(st['schema'])} · Methodology {esc(st['methodology'])}</p>
<h2>Status</h2>
<p>Last run {ts(st['generated_ts'])}. Data through {ts(ctx.index['generated_from'])}.</p>
<div class="scroll"><table><thead><tr><th>Zone</th><th>Day-ahead through</th><th>Imbalance through</th><th>Last poll</th></tr></thead><tbody>{srows}</tbody></table></div>
<h2>All zones, latest graded day</h2>
{latest_scores_table(ctx, rel)}
<h2>Next decision</h2>
{latest_forecasts_table(ctx, rel)}
{''.join(zone_blocks)}
<h2>Definitions</h2>
{definitions(ctx)}"""
    return layout(ctx, "benchmarks/", "Benchmarks", body)


def page_docs(ctx, has_report):
    def body(rel):
        report = (f'<a href="{rel("docs/report.pdf")}">The 2020–2026 retrospective</a> (PDF)'
                  if has_report else "The 2020–2026 retrospective (PDF) is not published yet.")
        return f"""<h1>Docs</h1>
<ul>
<li><a href="{rel('docs/methodology/')}">Methodology</a></li>
<li><a href="{rel('docs/data/')}">Data interface</a></li>
<li>{report}</li>
</ul>"""
    return layout(ctx, "docs/", "Docs", body)


def page_methodology(ctx):
    def body(rel):
        return md(content("methodology.md"), rel) + "<h2>The five benchmarks</h2>" + definitions(ctx)
    return layout(ctx, "docs/methodology/", "Methodology", body)


def page_data(ctx):
    def body(rel):
        idx = ctx.index
        base = f"{SITE_URL}/{DATA_PATH}"
        files = "".join(
            f'<tr><td>{data_link(rel, "v1/" + f["name"], f["name"])}</td><td class="n">{f["bytes"]:,}</td>'
            f'<td><code>{f["sha256"]}</code></td></tr>' for f in idx["files"])
        def cols(d):
            return "<dl>" + "".join(f"<dt><code>{esc(k)}</code></dt><dd>{esc(v)}</dd>" for k, v in d.items()) + "</dl>"
        return f"""<h1>Data interface</h1>
<p class="lead">Files over HTTPS. There is no query interface.</p>
<p>Base address: <code>{base}</code></p>
<ul>
<li>Unit: {esc(idx['unit'])}.</li>
<li>Granularity: {esc(idx['granularity'])}.</li>
<li>Terms: {esc(idx['terms'])}</li>
<li>Heartbeat: {data_link(rel, 'status.xml', 'status.xml')}, rewritten by every run.</li>
</ul>
{md(content('data.md'), rel)}
<h2>Files</h2>
<div class="scroll"><table><thead><tr><th>File</th><th>Bytes</th><th>sha256</th></tr></thead><tbody>
<tr><td>{data_link(rel, 'v1/index.json', 'index.json')}</td><td></td><td>the map: vocabulary, definitions, files</td></tr>
<tr><td>{data_link(rel, 'v1/zones.json', 'zones.json')}</td><td></td><td>per zone: EIC, timezone, currencies, first and last day</td></tr>
{files}</tbody></table></div>
<h2>Score columns</h2>
{cols(idx.get('columns', {}))}
<h2>Benchmark columns</h2>
{definitions(ctx)}
<h2>Forecast columns</h2>
{cols(idx.get('forecast_columns', {}))}"""
    return layout(ctx, "docs/data/", "Data interface", body)


def page_news(ctx):
    def body(rel):
        parts = ["<h1>News</h1>"]
        for e in ctx.news:
            v = e["versions"]
            tag = ""
            if v:
                tag = '<p class="version">' + " · ".join(
                    f"{k.capitalize()} {v[k]}" for k in ("schema", "methodology") if k in v) + "</p>"
            parts.append(f'<article id="{e["date"]}"><h2>{e["date"]}</h2>{tag}'
                         f'{md(chr(10).join(e["lines"]), rel)}</article>')
        return "\n".join(parts)
    return layout(ctx, "news/", "News", body)


def page_content(ctx, path, name, title):
    return layout(ctx, path, title, lambda rel: md(content(name), rel))


def sitemap(paths):
    urls = "".join(f"<url><loc>{SITE_URL}/{p}</loc></url>" for p in paths)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')


# ---------------------------------------------------------------- build

def build(out):
    ctx = Ctx()
    ctx.status = read_status()
    ctx.m = ctx.status["methodology"]
    ctx.index = json.loads((DATA / "v1" / "index.json").read_text(encoding="utf-8"))
    verify_files(ctx.index)
    ctx.zones = json.loads((DATA / "v1" / "zones.json").read_text(encoding="utf-8"))
    ctx.zone_codes = sorted(ctx.zones)
    ctx.scores = {z: read_csv(f"{z}_scores.csv") for z in ctx.zone_codes}
    ctx.forecasts = {z: read_csv(f"{z}_forecasts.csv") for z in ctx.zone_codes}
    ctx.latest_score = {r["zone"]: r for r in read_csv("scores-latest.csv")}
    ctx.latest_forecast = {r["zone"]: r for r in read_csv("forecasts-latest.csv")}
    ctx.news = read_news()
    check_versions(ctx.news, ctx.status)

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    has_report = (CONTENT / "report.pdf").exists()
    pages = {
        "": page_home(ctx),
        "benchmarks/": page_benchmarks(ctx),
        "docs/": page_docs(ctx, has_report),
        "docs/methodology/": page_methodology(ctx),
        "docs/data/": page_data(ctx),
        "news/": page_news(ctx),
        "about/": page_content(ctx, "about/", "about.md", "About"),
        "chuchueva/": page_content(ctx, "chuchueva/", "chuchueva.md", "Irina Chuchueva"),
        "contact/": page_content(ctx, "contact/", "contact.md", "Contact"),
        "support/": page_content(ctx, "support/", "support.md", "Support"),
    }
    for path, text in pages.items():
        target = out / path / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    shutil.copyfile(SRC / "style.css", out / "style.css")
    (out / "img").mkdir()
    for f in sorted((SRC / "img").iterdir()):
        if f.is_file() and f.name not in NOT_COPIED and not f.name.startswith("."):
            shutil.copyfile(f, out / "img" / f.name)
    shutil.copyfile(SRC / "img" / "og.png", out / "og.png")
    if has_report:
        shutil.copyfile(CONTENT / "report.pdf", out / "docs" / "report.pdf")
    shutil.copytree(DATA, out / DATA_PATH)
    (out / "sitemap.xml").write_text(sitemap(sorted(pages)), encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n",
                                    encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_site")
    args = ap.parse_args()
    try:
        build(Path(args.out))
    except BuildError as e:
        print(f"BUILD FAILED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
