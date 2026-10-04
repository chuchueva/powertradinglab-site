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
UNIT = "EUR per 1 MW of trading quantity for each 15-minute interval, summed over the delivery day"

NAV = [
    ("about/", "About"),
    ("benchmarks/", "Benchmarks"),
    ("docs/", "Docs"),
    ("news/", "News"),
    ("support/", "Support"),
    ("contact/", "Contact"),
]


# The stylesheet address changes whenever its content does, so browsers and the
# Cloudflare cache never serve an old style.css with new pages. Deterministic.
CSS_VERSION = hashlib.sha256((SRC / "style.css").read_bytes()).hexdigest()[:10]


REPORT = "chuchueva_2026_europe_power_trade_opportunities_2020_2026_eng.pdf"   # content/ -> /docs/
RUN_TIMES_UTC = ("09:40", "14:00")   # the server's schedule (SITE.md)


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
        return f"Decided on all {ptu} 15-minute intervals."
    if why and n == ptu:
        return f"Forecast declined: no decision on any of the {ptu} 15-minute intervals because {reason_text(why)}."
    if why:
        return f"Partly declined: {n} of {ptu} 15-minute intervals without a decision because {reason_text(why)}."
    if n == ptu:
        return f"The signal did not form on any of the {ptu} 15-minute intervals; nothing was refused."
    return f"The signal did not form on {n} of {ptu} 15-minute intervals; nothing was refused."


def score_statements(r, tzname):
    out = []
    ptu = int(r["ptu"])
    pwa = int(r["ptu_with_action"] or 0)
    full = full_ptu(tzname, r["delivery_day"])
    if ptu < full:
        out.append(f"The source published {ptu} of {full} 15-minute intervals; the day is scored on the {ptu} that exist.")
    if pwa == 0:
        out.append("No decision was issued for this day, so there is no trailing-bias result. "
                   "The four market values are scored regardless.")
    elif pwa < ptu:
        out.append(f"A decision covered {pwa} of {ptu} 15-minute intervals; trailing bias is a sum over those {pwa}.")
    return out


# ---------------------------------------------------------------- markdown

def md(text, rel):
    """A small markdown subset: # headings, paragraphs, - lists, ``` blocks,
    `code`, - and 1. lists, **bold**, *italic*, [text](url), ![alt](url){width=N}, and
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
            w = re.search(r"\{width=(\d+)\}", lines[0])
            style = f' style="grid-template-columns: {w.group(1)}px 1fr"' if w else ""
            body = (f'<div class="side"{style}><div class="side-media">{md(lines[0], rel)}</div>'
                    f'<div class="side-text">{md(chr(10).join(lines[1:]), rel)}</div></div>')
        else:
            body = f'<div class="{esc(name)}">{md(inner, rel)}</div>'
        blocks.append(body)
        return f"\x00{len(blocks) - 1}\x00"

    text = re.sub(r"^:::\s*([\w-]+)\s*\n(.*?)\n:::\s*$", block, text, flags=re.S | re.M)

    out, para, items, code = [], [], [], None
    kind = ["ul"]

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()
        if items:
            tag = kind[0]
            out.append(f"<{tag}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{tag}>")
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
        elif line.startswith("- ") or re.match(r"\d+\.\s", line):
            new = "ul" if line.startswith("- ") else "ol"
            if para or (items and kind[0] != new):
                flush()
            kind[0] = new
            items.append(line[2:] if new == "ul" else re.sub(r"^\d+\.\s+", "", line))
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
    logo = f'<img src="{rel("img/logo.svg")}" alt="PowerTradingLab" width="584" height="88">'
    # the home page does not link to itself
    brand = f'<span class="brand">{logo}</span>' if path == "" else f'<a class="brand" href="{rel("")}">{logo}</a>'
    st = ctx.status
    footer = (
        f'<p>Schema {esc(st["schema"])} · Methodology {esc(st["methodology"])} · '
        f'Last run {utc_time(st["generated_ts"])}, next run {utc_time(next_run(st["generated_ts"]))}</p>'
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
<link rel="stylesheet" href="{rel('style.css')}?v={CSS_VERSION}">
</head>
<body>
<header><div class="wrap">{brand}<nav>{nav}</nav></div></header>
<main class="wrap">
{body(rel)}
</main>
<footer><div class="wrap">{footer}</div></footer>
{LOCAL_TIME_JS}
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
            sign = "pos" if float(v) > 0 else "neg" if float(v) < 0 else ""
            cells.append(f'<td class="n {sign}">{num(v)}</td>')
    return "".join(cells)


# Display names. zones.json may carry its own "name", which wins; otherwise this
# table; otherwise the code alone.
ZONE_NAMES = {
    "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "CH": "Switzerland",
    "CZ": "Czechia", "DE-LU": "Germany–Luxembourg", "DK1": "Denmark West",
    "DK2": "Denmark East", "EE": "Estonia", "ES": "Spain", "FI": "Finland",
    "FR": "France", "GR": "Greece", "HR": "Croatia", "HU": "Hungary",
    "IT-North": "Italy North", "LT": "Lithuania", "LV": "Latvia", "NL": "Netherlands",
    "NO1": "Norway 1", "NO2": "Norway 2", "NO3": "Norway 3", "NO4": "Norway 4",
    "NO5": "Norway 5", "PL": "Poland", "PT": "Portugal", "RO": "Romania",
    "RS": "Serbia", "SE1": "Sweden 1", "SE2": "Sweden 2", "SE3": "Sweden 3",
    "SE4": "Sweden 4", "SI": "Slovenia", "SK": "Slovakia",
}


def zone_name(ctx, z):
    name = ctx.zones.get(z, {}).get("name") or ZONE_NAMES.get(z)
    return f"{esc(name)} ({z})" if name else z


def latest_scores_table(ctx, rel):
    head = "".join(f'<th class="n">{lbl}</th>' for _, lbl in VALUES)
    rows, notes = [], []
    for z in ctx.zone_codes:
        r = ctx.latest_score.get(z)
        if r is None:
            rows.append(f'<tr><th>{z}</th>'
                        f'<td colspan="9" class="muted">No scored day published yet.</td></tr>')
            continue
        if r["methodology_version"] != ctx.m:
            cells = f'<td>{r["delivery_day"]}</td>' + not_comparable(r, 8)
        else:
            cells = (f'<td>{r["delivery_day"]}</td><td class="nw">{esc(r["pass"])}</td>' + value_cells(r) +
                     f'<td class="n">{r["ptu"]} / {r["ptu_with_action"]}</td>'
                     f'<td>{data_link(rel, r["source_file"], "score")}</td>')
            for s in score_statements(r, ctx.zones[z]["timezone"]):
                notes.append(f"<li><strong>{z} {r['delivery_day']}.</strong> {s}</li>")
        rows.append(f'<tr><th>{z}</th>{cells}</tr>')
    note_html = f'<ul class="notes">{"".join(notes)}</ul>' if notes else ""
    return (f'<div class="scroll"><table><caption>{UNIT}.</caption>'
            f'<thead><tr><th>Zone</th><th>Delivery day</th><th>Pass</th>{head}'
            f'<th class="n">15-minute intervals<br>scored / forecasted</th><th>File</th></tr></thead>'
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
    return ('<div class="scroll"><table><caption>Forecast action of the &ldquo;simplest trading strategy&rdquo; '
            'for each interval: +1 means buy on DA, &minus;1 means sell on DA, NA means there is not enough '
            'data for a decision.</caption>'
            '<thead><tr><th>Zone</th><th>Delivery day</th><th class="n">Buy</th><th class="n">Sell</th>'
            '<th class="n">No action</th><th>Published</th><th>File</th></tr></thead>'
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

    head = "".join(f'<th class="n">{lbl}</th>' for _, lbl in VALUES)
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
                scell = '<td colspan="6" class="muted">Not scored yet.</td>'
            else:
                scell = '<td colspan="6" class="muted">Not scored: no score was published for this day.</td>'
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
    return (f'<div class="scroll"><table><caption>Newest days first. Decision: number of 15-minute intervals buy / sell / '
            f'no action. Values: {UNIT}.</caption>'
            f'<thead><tr><th>Delivery day</th><th class="n">Decision</th>{head}'
            f'<th class="n">15-minute intervals<br>scored / forecasted</th></tr></thead>'
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

def latest_news(ctx, rel):
    if not ctx.news:
        return ""
    e = ctx.news[0]
    return (f'<h2>Latest news</h2><article class="news-latest"><p class="meta">{e["date"]}</p>'
            f'{md(chr(10).join(e["lines"]), rel)}'
            f'<p><a href="{rel("news/")}#{e["date"]}">All news</a></p></article>')


KEY_DEFINITIONS = """<dl>
<dt>&ldquo;Speculative Fat&rdquo;: how much a market holds &mdash; <code>extractable_value</code></dt>
<dd>Imagine a trader with a crystal ball who knows in advance both the day-ahead (DA) and the imbalance (IM) prices. For every 15-minute interval this trader buys or sells 1 MW at DA and closes the position at the IM price. The profit of such a trader is <code>extractable_value</code>.</dd>
<dt>&ldquo;Simplest trading strategy&rdquo;: how much of market fat is repeatable &mdash; <code>trailing_bias_value</code></dt>
<dd>Imagine a trader with no model, only a habit. For each hour of the day the trader looks at the previous three days, sees whether buying or selling at DA paid better in that hour, and follows the same pattern bidding for tomorrow. The profit of such a trader is <code>trailing_bias_value</code>.</dd>
</dl>"""

EXTRA_DEFINITIONS = """<dl>
<dt>Passive DA buy &mdash; <code>passive_da_buy_value</code></dt>
<dd>Imagine a trader who always buys 1 MW at DA in every 15-minute interval and closes the position at the IM price. The profit of such a trader is <code>passive_da_buy_value</code>.</dd>
<dt>Passive DA sell &mdash; <code>passive_da_sell_value</code></dt>
<dd>Imagine a trader who always sells 1 MW at DA in every 15-minute interval and closes the position at the IM price. The profit of such a trader is <code>passive_da_sell_value</code>. Read together with <code>passive_da_buy_value</code>, it shows whether there is a persistent bias between DA and IM prices.</dd>
<dt>Adverse &mdash; <code>adverse_value</code></dt>
<dd>Imagine the trader with the crystal ball again, now choosing the wrong side in every interval to lose as much as possible. The profit of such a trader is <code>adverse_value</code>. Where a zone settles imbalance at a single price, it is the exact mirror of <code>extractable_value</code>.</dd>
</dl>"""


def next_run(generated_ts):
    """The next scheduled run after the last one, from RUN_TIMES_UTC."""
    if not generated_ts:
        return ""
    day, hm = generated_ts[:10], generated_ts[11:16]
    later = [t for t in RUN_TIMES_UTC if t > hm]
    if later:
        return f"{day}T{later[0]}:00Z"
    d = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
    return f"{d}T{RUN_TIMES_UTC[0]}:00Z"


def utc_time(x):
    """A UTC instant; a small script adds the viewer's local time beside it.
    Without JavaScript the UTC value stands alone, which is complete."""
    return f'<time class="lt" datetime="{x}">{ts(x)}</time>'


LOCAL_TIME_JS = """<script>
document.querySelectorAll("time.lt").forEach(function (t) {
  var d = new Date(t.getAttribute("datetime"));
  if (isNaN(d)) return;
  t.insertAdjacentText("beforeend", " (" + d.toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"}) + " local time)");
});
</script>"""


def zone_link(rel, z):
    return f'<a href="{rel("benchmarks/")}#{z}">{z}</a>'


def home_scores_table(ctx, rel):
    rows = []
    for z in ctx.zone_codes:
        r = ctx.latest_score.get(z)
        if r is None:
            rows.append(f'<tr><th>{zone_link(rel, z)}</th><td colspan="5" class="muted">No scored day yet.</td></tr>')
            continue
        if r["methodology_version"] != ctx.m:
            rows.append(f'<tr><th>{zone_link(rel, z)}</th><td>{r["delivery_day"]}</td>{not_comparable(r, 4)}</tr>')
            continue
        cells = []
        for key in ("extractable_value", "trailing_bias_value"):
            v = r[key]
            if v == "":
                cells.append('<td class="n muted">no decision</td>')
            else:
                sign = "pos" if float(v) > 0 else "neg" if float(v) < 0 else ""
                cells.append(f'<td class="n {sign}">{num(v)}</td>')
        rows.append(f'<tr><th>{zone_link(rel, z)}</th><td>{r["delivery_day"]}</td>{"".join(cells)}'
                    f'<td class="n">{r["ptu"]} / {r["ptu_with_action"]}</td>'
                    f'<td>{data_link(rel, r["source_file"], "score")}</td></tr>')
    return (f'<div class="scroll"><table><caption>{UNIT}.</caption>'
            '<thead><tr><th>Zone</th><th>Delivery day</th>'
            '<th class="n">Daily &ldquo;Speculative Fat&rdquo;<br>(Extractable)</th>'
            '<th class="n">Daily &ldquo;Simplest trading strategy&rdquo; PnL<br>(Trailing bias)</th>'
            '<th class="n">15-minute intervals<br>scored / forecasted</th><th>File</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def home_forecasts_table(ctx, rel):
    rows = []
    for z in ctx.zone_codes:
        r = ctx.latest_forecast.get(z)
        if r is None:
            rows.append(f'<tr><th>{zone_link(rel, z)}</th><td colspan="5" class="muted">No forecast yet.</td></tr>')
            continue
        if r["methodology_version"] != ctx.m:
            rows.append(f'<tr><th>{zone_link(rel, z)}</th><td>{r["delivery_day"]}</td>{not_comparable(r, 4)}</tr>')
            continue
        rows.append(f'<tr><th>{zone_link(rel, z)}</th><td>{r["delivery_day"]}</td><td>{ts(r["knownby_ts"])}</td>'
                    f'<td class="n">{r["ptu_buy"]}</td><td class="n">{r["ptu_sell"]}</td>'
                    f'<td>{data_link(rel, r["source_file"], "forecast")}</td></tr>')
    return ('<div class="scroll"><table><caption>Forecast action of the &ldquo;simplest trading strategy&rdquo; '
            'for each interval: +1 means buy on DA, &minus;1 means sell on DA, NA means there is not enough '
            'data for a decision.</caption>'
            '<thead><tr><th>Zone</th><th>Delivery day</th><th>Published</th>'
            '<th class="n">Buy</th><th class="n">Sell</th><th>File</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def page_home(ctx):
    def body(rel):
        st = ctx.status
        b = ctx.index["benchmarks"]
        return f"""<div class="intro">{md(content('home.md'), rel)}</div>
<h2>Latest scored day</h2>
{home_scores_table(ctx, rel)}
<h2>Next trading action (Trailing Bias Value)</h2>
{home_forecasts_table(ctx, rel)}
<h2>Two key benchmarks</h2>
{KEY_DEFINITIONS}
<p><a href="{rel('benchmarks/')}">Zones details</a> · <a href="{rel('docs/')}">Methodology and Data Interface</a></p>
{latest_news(ctx, rel)}"""
    return layout(ctx, "", "", body)


def page_benchmarks(ctx):
    def body(rel):
        st = ctx.status
        srows = "".join(
            f"<tr><th>{z}</th><td>{ts(st['areas'].get(z, {}).get('da_through', ''))}</td>"
            f"<td>{ts(st['areas'].get(z, {}).get('im_through', ''))}</td>"
            f"<td>{ts(st['areas'].get(z, {}).get('last_poll', ''))}</td></tr>"
            for z in ctx.zone_codes)
        zone_index = " · ".join(f'<a href="#{z}">{zone_name(ctx, z)}</a>' for z in ctx.zone_codes)
        zone_blocks = []
        for z in ctx.zone_codes:
            zi = ctx.zones[z]
            meta = (f'<span class="h-meta">EIC <code>{esc(zi.get("eic", ""))}</code> · '
                    f'{esc(zi.get("timezone", ""))}</span>')
            # method_note() is kept for later: at launch the page says nothing about
            # earlier methodologies (owner's call, 2026-10-02).
            zone_blocks.append(
                f'<section id="{z}"><h2>{zone_name(ctx, z)} {meta}</h2>'
                f'{zone_days_table(ctx, z, rel)}<h3>Archive</h3>{downloads(ctx, z, rel)}</section>')
        return f"""<h1>Benchmarks</h1>
<p class="version">Schema {esc(st['schema'])} · Methodology {esc(st['methodology'])}</p>
<p class="zones">Zones: {zone_index}</p>
<h2>Status</h2>
<p>Last run {ts(st['generated_ts'])}. Data through {ts(ctx.index['generated_from'])}.</p>
<div class="scroll"><table><thead><tr><th>Zone</th><th>Day-ahead through</th><th>Imbalance through</th><th>Last poll</th></tr></thead><tbody>{srows}</tbody></table></div>
<h2>All zones, latest scored day</h2>
{latest_scores_table(ctx, rel)}
<h2>Next trading action (Trailing Bias Value)</h2>
{latest_forecasts_table(ctx, rel)}
{''.join(zone_blocks)}
<h2>Definitions</h2>
<h3>Key</h3>
{KEY_DEFINITIONS}
<h3>Extra</h3>
{EXTRA_DEFINITIONS}"""
    return layout(ctx, "benchmarks/", "Benchmarks", body)


def demote(text):
    """Shift markdown headings one level down, for a file shown as a section."""
    return re.sub(r"^(#{1,5})(\s)", r"#\1\2", text, flags=re.M)


def data_section(ctx, rel):
    idx = ctx.index
    base = f"{SITE_URL}/{DATA_PATH}"
    files = "".join(
        f'<tr><td>{data_link(rel, "v1/" + f["name"], f["name"])}</td><td class="n">{f["bytes"]:,}</td>'
        f'<td><code>{f["sha256"]}</code></td></tr>' for f in idx["files"])

    def cols(d):
        return "<dl>" + "".join(f"<dt><code>{esc(k)}</code></dt><dd>{esc(v)}</dd>" for k, v in d.items()) + "</dl>"
    return f"""<p class="lead">Files over HTTPS. There is no query interface.</p>
<p>Base address: <code>{base}</code></p>
<ul>
<li>Unit: {esc(idx['unit'])}.</li>
<li>Granularity: {esc(idx['granularity'])}.</li>
<li>Terms: {esc(idx['terms'])}</li>
<li>Heartbeat: {data_link(rel, 'status.xml', 'status.xml')}, rewritten by every run.</li>
</ul>
{md(demote(content('data.md')), rel)}
<h3>Files</h3>
<div class="scroll"><table><thead><tr><th>File</th><th class="n">Bytes</th><th>sha256</th></tr></thead><tbody>
<tr><td>{data_link(rel, 'v1/index.json', 'index.json')}</td><td></td><td>the map: vocabulary, definitions, files</td></tr>
<tr><td>{data_link(rel, 'v1/zones.json', 'zones.json')}</td><td></td><td>per zone: EIC, timezone, currencies, first and last day</td></tr>
{files}</tbody></table></div>
<h3>Score columns</h3>
{cols(idx.get('columns', {}))}
<h3>Benchmark columns</h3>
<p>As stated in <code>index.json</code>, which travels with the data. Plain-language definitions are under <a href="#methodology">Methodology</a>.</p>
{definitions(ctx)}
<h3>Forecast columns</h3>
{cols(idx.get('forecast_columns', {}))}"""


def page_docs(ctx, has_report):
    def body(rel):
        report = (f'<a href="{rel("docs/" + REPORT)}">The 2020–2026 retrospective</a> (PDF)'
                  if has_report else "The 2020–2026 retrospective (PDF) is not published yet.")
        method = re.sub(r"^#\s+.*\n?", "", content("methodology.md"), count=1)
        return f"""<h1>Docs</h1>
<ul>
<li><a href="#methodology">Methodology</a></li>
<li><a href="#data">Data interface</a></li>
<li>{report}</li>
</ul>
<section id="methodology"><h2>Methodology</h2>
{md(demote(method), rel)}
<h3>The five benchmarks</h3>
<h4>Key</h4>
{KEY_DEFINITIONS}
<h4>Extra</h4>
{EXTRA_DEFINITIONS}
</section>
<section id="data"><h2>Data interface</h2>
{data_section(ctx, rel)}
</section>"""
    return layout(ctx, "docs/", "Docs", body)


def redirect(path, target):
    """A permanent address that moved inside another page. Works without JS."""
    depth = path.count("/")
    url = "../" * depth + target
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Moved</title>
<link rel="canonical" href="{SITE_URL}/{target}">
<meta http-equiv="refresh" content="0; url={url}">
</head>
<body><p><a href="{url}">This page is now part of Docs.</a></p></body>
</html>
"""


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
    cls = "page-" + name.rsplit(".", 1)[0]
    def body(rel):
        html_ = md(content(name), rel)
        # a line "{{definitions}}" in any content page is replaced by the shared definitions
        html_ = html_.replace("<p>{{definitions}}</p>",
                              f"<h3>Key</h3>\n{KEY_DEFINITIONS}\n<h3>Extra</h3>\n{EXTRA_DEFINITIONS}")
        return f'<div class="{cls}">{html_}</div>'
    return layout(ctx, path, title, body)


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
    has_report = (CONTENT / REPORT).exists()
    pages = {
        "": page_home(ctx),
        "benchmarks/": page_benchmarks(ctx),
        "docs/": page_docs(ctx, has_report),
        "news/": page_news(ctx),
        "about/": page_content(ctx, "about/", "about.md", "About"),
        "chuchueva/": page_content(ctx, "chuchueva/", "chuchueva.md", "Irina Chuchueva"),
        "contact/": page_content(ctx, "contact/", "contact.md", "Contact"),
        "support/": page_content(ctx, "support/", "support.md", "Support"),
    }
    moved = {
        "docs/methodology/": redirect("docs/methodology/", "docs/#methodology"),
        "docs/data/": redirect("docs/data/", "docs/#data"),
    }
    for path, text in list(pages.items()) + list(moved.items()):
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
        shutil.copyfile(CONTENT / REPORT, out / "docs" / REPORT)
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
