# TradingLab — project handoff summary

Short brief to bring a new Claude/Cowork session up to speed on the TradingLab benchmark project. Written July 2026.

**The project began on 23 July 2026** — first commit at 12:32. Let us see how long it lives.

See `docs/MAP.md` for the shape of the codebase on one page. This document is
the reasoning behind it.

## START HERE (as of 2026-10-01)

**What exists.** The service runs unattended on a rented server in Nuremberg,
three timers a day, since 2026-09-26. Two zones are live: NL since August, RO
since 2026-09-28. Schema 6, methodology 3. 103 tests. Each run collects, decides
before the day-ahead gate, grades the finished day, writes frozen files that are
re-rendered and byte-compared on every later run, rebuilds the `outputs/v1`
reader interface (scores and forecasts), pushes a snapshot to a private backup
repository, and pushes the public data to the site repository.

**Where to look.**

- `docs/MAP.md` — the codebase on one page.
- **"The rules, in one place"**, immediately below — read before changing
  anything. Everything else in this file is the reasoning behind one of them.
- **"What is NOT done"** — the single canonical list of what is left. Other
  files point at it rather than keeping their own.
- `docs/HOSTING.md` — the machine, the schedule, the backup, how to restore.
- `docs/SITE.md` — the brief for the website, built in a separate session.
- `docs/ROMANIA.md` — the second zone, and the six decisions taken for it.

**House rules for working in here.**

- **No file is changed without the owner asking.** Discuss first, then edit.
- **The two version numbers in `settings.json` are raised BY HAND, by the owner.**
  Never by an assistant, never as part of another change.
- **`docs/` and `src/` belong to this session; `report/` belongs to the report
  session.** Do not edit across that line.
- **Never invent data** — rule 9, and the one that has been load-bearing more
  often than any other.

**Where the reasoning is, when a decision looks strange.** Almost every rule
here was written after something went wrong, and the section that states it says
what. The ones worth reading before touching the publication path: "The version
belongs to the ROW, not to the settings", "The publisher belongs to the row too",
"Scoring is driven by the STORE now", "The gate is per HOUR now" and "The log
reports a PASS, not a day". Two entries record conclusions that were WRONG and
were corrected — the backfill claim of 09-27 and the shadow-roster test — and
they are kept as entries rather than quietly edited, because how a wrong
conclusion got made is the useful part.

## The rules, in one place

Nine invariants. They compress the whole codebase: hold these and most of the
code can be re-derived by thinking, which is faster than reading it. Each is
explained in full further down; each is also guarded by a test.

1. **UTC only, tz-aware, everywhere.** Market-local time exists in exactly one
   file, `period.py`, and even there what leaves is the UTC instant.
2. **Two time entities, not three:** `delivery_ts` (the PTU) and `knownby_ts`
   (when the row became known). `current_ts` is the as-of cursor, not a third
   kind of time; in our own outputs it IS the `knownby_ts`.
3. **`as_of` is two steps:** keep `knownby_ts < current_ts`, THEN keep the max
   `knownby_ts` per key. Forgetting the second step is invisible until there are
   two versions, and then it silently corrupts.
4. **`as_of` OR `shift(2)`, never both.** They say the same thing; stacked, they
   lag the signal twice.
5. **The store keeps versions; collapsing happens at READ time.** The point is
   to be able to ask what was known at a past instant.
6. **Only changes are written.** So `knownby_ts` reads as "the first time we saw
   this value", and as-known / as-final are just the first and last row.
7. **EUR is a unit, not a rate** — 1.0, never looked up. Currency is always read
   from the document, never assumed.
8. **A delivery day is scored exactly twice:** as-known when it first settles
   complete, as-final after the 20th of the following month.
9. **Never invent data.** No FX forward-filled past the end of the file, no
   half-published day scored as whole, no signal defaulted to −1 when the window
   is short (`<NA>` instead). A gap is information.

## What the project is

A public, fully open family of speculative trading benchmarks for European power markets — think "S&P 500 for power trading". Benchmarks span day-ahead (DA), intraday auction (IDA) and imbalance (IM) segments across the largest European bidding zones. The family ranges from a fully passive benchmark to an ideal / perfect-foresight one; the gap between them is a "market potential" indicator.

Goals: transparency in an opaque domain, reputation-building, intellectual satisfaction. Not primarily profit. A paid tier (Python API, DRL model) is deferred to much later.

Owner: Irina Chuchueva — 19 yrs in power-market math modelling (RU then EU markets), 6 yrs building an algo-trading system for a Belgium-based firm (ended Feb 2026). Based in Yerevan. Works via an Armenian sole-proprietorship (IT).

### Funding philosophy — donations, NOT paywall (core principle)

Sustainability model is **voluntary donations, never a paywall**. The whole project stays open and free; a "support" option just lets people who value it chip in for hosting, domain, and — later — the compute/time that the harder maths (DRL etc.) will need. This is a stated PART of the project's identity, not an afterthought: openness is the brand, so funding must never gate data or bias the benchmark.

- Keep donations small and diffuse; disclose who funded what; funding must NOT influence methodology (a benchmark's whole value is its neutrality). A transparent public ledger turns this into a trust asset, not a liability.
- Platform choice is dominated by ONE constraint: getting paid out to Armenia. Most services pay via Stripe, which barely works in Armenia, so Armenia is usually absent from supported-country lists (GitHub Sponsors, Buy Me a Coffee, Ko-fi-via-Stripe). Realistic rails are **Payoneer and Wise**. Verify payout eligibility per platform before committing.
- Best fits to check first: **Open Collective** (public income/expense ledger — philosophically ideal; pays via a fiscal host, often Wise/PayPal) and **GitHub Sponsors** (natural since code is on GitHub, but Stripe-gated → likely waitlist for Armenia).
- Timing: reserve the handle/name now, but only launch the "support" button once the витрina/prototype is live (conversion is ~0 before there's something to show). Low expectations — target is "covers hosting + domain".
- Donations are income for the Armenian IP; keep the books clean, confirm with a local accountant if amounts grow (not tax advice).

### Launch strategy — REPORT-FIRST (decided)

Ship a big PDF report of the findings FIRST, while the live daily workflow is still being
proven stable over time. Rationale: delivers value immediately, carries no
"service-broke-on-day-one" risk (a dated, static, reproducible artifact), establishes the
brand/mission (open, transparent). Gives the first (few, known) donors something concrete now.
Publish + email to the owner's contacts; also host the PDF on the project site. Owner's framing:
"not publishing these numbers would be a crime" — 1.5 weeks of work already yields a map
traders lack; the cost of silence is other people's wasted months.

- FORMAT: an industry / corporate-style report (like an exchange or data-aggregator
  publishes), single-topic, tight, in **LaTeX**. NOT a scientific paper — no literature
  review etc. (The owner's actual academic paper is separate and awaiting publication
  approval, ~6 months; this report is deliberately lightweight and fast.)
- GRANULARITY: narrative, method and conclusions at the ANNUAL level only. For readers who
  want to dig deeper, optionally ship a monthly-per-zone data file as an appendix/dataset —
  data only, not described in the text.

- The report is a FROZEN artifact: dated, versioned, immutable (fits the methodology).
  Built from the current `yearly.xlsx` (2020-2026, ~44 zones, benchmarks always_buy/sell,
  ideal, devil, stat_action).
- Suggested structure: (1) the problem — traders fly blind, backtests catch stale alpha;
  (2) method — DA-IM envelope, per-1-MW, ideal/devil/always/stat_action, causal; (3) the
  two axes — FATNESS (ideal) vs TRADEABILITY (stat_action + bias persistence), with the
  taxonomy: tradeable single+persistent (NOx, SEx, SI-post-2023, NO1), dead dual+wide-band
  (ES, CH-pre-2026, SI-pre-2023), big-but-mirage (BE, flip); (4) regime transitions
  (dual<->single table) and alpha decay (RO 2020->2025, crisis-2022 fatness); (5) per-zone
  tables + one-line verdicts; (6) caveats + what the live service will add. Attribution to
  ENTSO-E / ECB throughout; publish derived results, not raw DA price series.
- Timing: report can go out NOW from the xlsx; the live workflow (NL first) matures in
  parallel and becomes the follow-on.
- CROSS-LINK: for the un-tradeable zones (ES and similar), the report frames the finding as
  "arriving imbalanced at gate closure is a systematic loss in BOTH directions" (both
  `-always_buy` and `-always_sell` positive = a cost every year) — so PRE-delivery balancing
  via IDA / continuous order book is a necessity, not an optimisation. Point those readers to
  pre-delivery execution tools (cite the owner's Nord Pool latency / order-book paper). Do
  NOT edit that academic paper; the connection lives only in the report.

## The palette (official, 2026-09-23)

One set of colours for everything the project shows anyone — the report, the
site, any chart, any diagram, anything coloured that comes out of code here.
The owner's definitions, verbatim, as the report uses them:

```latex
\definecolor{tlaccent}{HTML}{157A7F}   % teal   - section headings, rules
\definecolor{tlink}{HTML}{0E2A33}      % ink    - subsection headings, body accents
\definecolor{tlamber}{HTML}{E39B2F}    % amber  - second accent, sparingly
\definecolor{tlgrey}{HTML}{6B7780}     % muted grey - metadata, header/footer
\definecolor{tlrule}{HTML}{D8DEE0}     % hairlines
```

| name | hex | for |
|---|---|---|
| `tlaccent` | `#157A7F` | teal: section headings, rules, the primary series |
| `tlink` | `#0E2A33` | ink: subsection headings, body accents, text-weight marks |
| `tlamber` | `#E39B2F` | amber: the second accent — sparingly, for contrast against teal |
| `tlgrey` | `#6B7780` | muted grey: metadata, header and footer, secondary annotation |
| `tlrule` | `#D8DEE0` | hairlines, gridlines, borders |

The hex codes are the source; the LaTeX names are one binding of them, and the
same five travel into matplotlib, HTML and SVG unchanged. **Anything coloured
that we generate in code uses these and nothing else** — no library default
palette, no ad-hoc hex. A chart that needs more than two series needs a
decision about the palette, not an improvised sixth colour.

Deliberately small: two accents, one of them used rarely, and three neutrals.
A benchmark's job is to be read, and a reader who has learned that teal is us
and amber is the exception can read the next chart faster than the first.

The decay charts already in the report are the owner's to repaint.

## Method decisions (locked)

- **Unit of analysis:** bidding zone (not country). If a participant sits in a complex/multi-area zone, that's an explicit documented assumption, not something we try to handle now (possible paid custom work later).
- **Time — UTC ONLY, NO EXCEPTIONS:** every timestamp we store (in any DataFrame, feather, parquet, CSV, filename) is UTC and tz-aware. There is no market-local column anywhere in stored data. CET/CEST is allowed at exactly ONE place — computing the market-day period bounds for API requests (`period.py`) — and even there the emitted string is the UTC instant. If a timestamp is not UTC, it is a bug.
- **Time anchors (UTC):** DA auction (SDAC/Euphemia) gate closure = 12:00 CET → **10:00 UTC in summer (CEST), 11:00 UTC in winter (CET)**; results published ~12:45–12:57 CET (~10:45/11:45 UTC). So when deciding for delivery day D on D-1 morning (before gate), the freshest FULLY-settled IM day is D-2 → a causal daily signal lags by 2 market days. Yesterday's IM becomes available (`as-known`, first snapshot) by ~10/11 UTC.
- **Point-in-time correctness (as-of), the canonical anti-lookahead rule:** do NOT build lags with `shift()` in the compute core. Instead filter `knownby_ts < current_ts`, so the calculation only ever sees data that was actually published by `current_ts`. The compute core is IDENTICAL for backtest and live — only `current_ts` differs (backtest iterates it; live uses `datetime.now(timezone.utc)`). This is heavier than shift() but keeps backtest == live and is robust to irregular publication and to VERSIONING. With ≥2 IM versions per `delivery_ts` (as-known / as-final), as-of = filter `knownby_ts < current_ts` THEN keep the row with the max `knownby_ts` per (area_eic, delivery_ts). Forgetting that second step is the main risk. Wrap in an `as_of(data, current_ts)` helper; `shift(2)` is only an acceptable shortcut for the CURRENT single-version backtest.
- **Resolution:** we store 15-min throughout, upsampling whatever the source sends. Most zones moved to native 15-min DA on 2025-10-01 (the SDAC MTU change), but **not all did** — Albania still publishes hourly, confirmed by its TSO (see `ENTSOE.md`). Resolution is therefore read from each document, never assumed from a date.
- **Frozen history:** published values are immutable, versioned, timestamped. Never silently revised.
- **Two value versions per series:** `calc_iteration = 0` (as-known, snapshot at ~T+1) and `= 1` (as-final, snapshot later once finals settle). ENTSO-E does NOT expose an intermediate/final flag in the XML, so the difference is found by re-fetching and comparing, not by reading a field. The divergence between the two is itself a planned indicator.
- **WHEN to take the as-final snapshot (Irina, market practice):** IM prices are
  revised up to FINAL by the **15th of the month following delivery** — i.e. up to
  ~45 days after a delivery day early in the month. So `calc_iteration = 1` for
  delivery month M is snapshotted AFTER the 15th of M+1, not on a fixed day-lag.
  Until that snapshot exists, the size of the revision is unmeasurable and any
  statement about it is speculation. Note also that ENTSO-E sets no deadline for
  the FIRST publication either ("as soon as possible; intermediate figures are
  published if final prices are not available") — so the publication delay is an
  empirical quantity we measure, never a constant we can look up.
- **Live pnl is as-of pnl.** What a trader sees at `current_ts` is computed from
  the IM values known then, not from finals that land weeks later. That is the
  number the workflow publishes. The as-known vs as-final gap is a SEPARATE,
  later analysis (the divergence indicator), not a correction to the live number.
- **Dual-price IM zones (e.g. NL):** store BOTH prices (long/A04, short/A05) separately, never average.

## Architecture (three layers, kept separate)

1. **Ingestion** (`ingest.py`) — universal fetch: calls the API, saves the RAW bytes to `data/raw/YYYY/MM/` exactly as received (XML for DA, zip for IM), writes a provenance sidecar. Does NOT parse. Filename encodes doc/zone/period/fetch-time so the two snapshot versions are distinguishable by filename. Filed by FETCH month (a request may span a month boundary, but can only be made at one instant): five polls a day is ~7300 files a year, and the trouble with that is the directory entry count, not the bytes. Nothing scans this tree — the filename carries the whole request — so files written under the old flat layout stay where they are, and archiving a past year is moving one folder. A REFUSED request is saved the same way (`ERROR_*.txt` plus its own sidecar, `ok: false`): a failure is an event of exactly the same kind as a success, and it belongs with the responses, not in the logs — `data/raw` is what the source said, `logs/` is what we did. The log line lifts the one human sentence out of the response, since ENTSO-E answers an outage with an 18 KB styled page that is almost entirely base64 logos (seen 2026-08-06: "Service Temporarily Unavailable — scheduled maintenance", both documents, one poll; the next poll simply caught up).
2. **Computation** (`parse_da.py`, `parse_im.py`) — pure functions, raw file in, DataFrame out. No network. This is where A03 forward-fill and quality counting live.
3. **Publication** — static site + flat files (later). No backend, no DB, no dashboard until users ask. (Explicit lesson from the prior project: 84% of effort went to infrastructure, only 16% to the actual alpha — do NOT repeat that.)

Storage: Parquet for series; CSV for published results.

### History cache (feather) — dev convenience, NOT source of truth

Owner's workflow: once the File Library archive is parsed, concatenate the WHOLE
history into one long DataFrame per product and cache it as feather. All 5
benchmarks then read straight from feather instead of re-parsing every run.

- IMPLEMENTED. `build_history.py` (publication/cache layer, separate from the pure
  parsers) walks `data/archive/`, runs the File Library parsers over every month for
  ALL areas, concatenates per product, and writes to `data/processed/`. Run:
  `uv run python src/build_history.py [da|im|load|all]`.
- Three tables, kept SEPARATE (join in the benchmark, not the cache). One row per
  15-min MTU per area. All timestamps UTC tz-aware (asserted before writing):
    - `history_da.feather`   : delivery_ts, knownby_ts, area, area_eic, price_da
    - `history_im.feather`   : delivery_ts, knownby_ts, area, area_eic, currency,
                               price_im_pos, price_im_neg
    - `history_load.feather` : delivery_ts, knownby_ts, area, area_eic, area_type,
                               load_mw
- Area identity: `area_eic` = canonical EIC (the de-dup / join key); `area` = human
  readable short code from File Library AreaMapCode (NL, BE, DE_LU, SE3, IT-NORTH, DK1…).
  Storing all areas + an `area` column means adding zones needs no rebuild.
- Cross-boundary de-dup on (area_eic, delivery_ts) keeping latest UpdateTime.
- DA verified: 10.77M rows, 2020-01 → 2026-07, 0 dups/NaN, and NL matches the live API
  price exactly (File Library and API DA are interchangeable).
- Benchmarks will import a thin `load_history()` that only reads feather.
- The feather cache is disposable — rebuildable any time from `data/archive/` + the
  parsers, which remain the source of truth. It is NOT the "frozen history" in the
  methodology sense. Lives under `data/` so it's already git-ignored.
- Arrow/feather preserves tz-aware UTC natively, consistent with the UTC-only rule
  (needs `pyarrow`, present in the mac `.venv`).

### Consumption (Actual Total Load 6.1.A) — zone-selection input

- Downloaded from File Library the same way (monthly zips, all zones per file). Used
  to size markets and decide which zones to add next, NOT part of the price benchmark.
- IMPLEMENTED via `parse_load_frame` + the LOAD branch of `build_history.py` ->
  `history_load.feather` (volume in MW, no currency). Same 15-min upsample pipeline.
- Load is published at MULTIPLE aggregation levels — `area_type` is BZN (zone), CTA
  (control area), CTY (country) or combinations. So one country can appear more than
  once (e.g. DK = two EICs: a CTY and a CTA). `area_type` keeps them apart. When
  eyeballing / sizing markets, FILTER to one level (usually CTY for country totals or
  BZN for zone-level) or the same country double-counts. ~60 areas per month.
- Only actual load (6.1.A) downloaded; 6.1.B day-ahead forecast not needed for selection.

### Currency & FX (BOTH legs — we always account for currency)

- **DA is NOT always EUR.** Most zones publish DA in EUR (SDAC), but some non-euro zones
  publish DA in local currency — confirmed: **UA_IPS DA is UAH** (price ~2000 UAH/MWh).
  IM likewise: many non-euro zones publish IM in local currency (PLN, CZK, HUF, RON, SEK,
  NOK, DKK, CHF, GBP, BGN, UAH, …). The File Library extract carries a `Currency` column
  on BOTH DA and IM — we keep it (`currency` column in both schemas) and store the price in
  its NATIVE currency. Never overwrite with EUR. (`parse_da_frame` keeps DA currency since
  the UA-UAH fix; before that it silently assumed EUR → UA numbers came out ~40× too big.)
- EUR conversion is a DERIVED step in `build_matrix` (benchmarks_core), SYMMETRIC across
  legs: each leg is converted by ITS OWN currency, `price_eur = price_local / rate`. A leg
  without a `currency` column defaults to EUR (rate 1.0), so the EUR-only NL store still
  works. The returned matrix is fully EUR (`price_da` is overwritten with its EUR value).
  Frozen history stays immutable; FX policy can change without touching source.
- **EUR is the UNIT, not a rate — set to 1.0 in `build_matrix`, never looked up.**
  The euro is worth one euro on every date that has ever existed or will, so this
  conversion needs no source. The FX table does carry EUR=1.0 rows, but only over
  the calendar of whichever ECB file was last downloaded — which is how the live
  NL run died on 2026-08-05 with `Missing FX rate for ['EUR']`: the store had been
  extended to 08-05 while `data/fx/` still ended 07-28. A euro zone must not
  depend on the freshness of a download it does not need. Numbers are unchanged
  (those rows were 1.0 anyway), so `yearly_fixed.csv` still reproduces exactly.
- **CLOSED 2026-09-22 — `src/fx.py` refreshes the rates on every run** (section
  "Exchange rates in the live path" below). What follows is the history.
  **Was OPEN: nothing refreshes `data/fx/`.** The ECB files are a manual download and
  go stale silently. NL never notices (EUR is set, not looked up), but any
  non-euro currency fails the moment the price data runs past the end of the FX
  file — a loud, specific error naming the uncovered dates and both spans, rather
  than the old message that named only the currency and sent us looking in the
  wrong place. The fix is an FX refresh step (`eurofxref-daily.xml` is one small
  request) plus a re-run of `parse_fx.py`; the sandbox cannot reach
  ecb.europa.eu, so it has to run on the owner's machine. Do NOT paper over it by
  forward-filling the last known rate past the end of the file: that would invent
  prices, and the whole point of the frozen history is that we do not.

  **FIRED 2026-09-03, and not where it was expected.** The prediction was that
  the first non-euro ZONE would trip it. What actually tripped it was the
  REPORT: refreshing the archive pushed the price history to 2026-08-31 while
  `data/fx/` still ended 2026-07-28, and `modelling/benchmarks.py` stopped with
  `IM in CZK: need 2026-07-29..2026-08-31, FX table has 1999-01-04..2026-07-28`.
  Nothing was wrong — the guard did its job, and the rewritten message named the
  currency, both spans and the remedy, so the fix took one download.

  Two consequences worth keeping. First, the trigger is not "a non-euro zone
  goes live" but "the price data outruns the FX file", and the report path
  outruns it every time the archive is refreshed — so the refresh step now has
  TWO reasons, not one, and is due before RO rather than with it. Second, this is
  the ordinary state of a manual dependency: it was documented, correct, and
  still went stale for five weeks without anyone noticing, because the only code
  that would have complained (a non-euro zone) did not exist yet.

  Refreshed by replacing `eurofxref-hist.xml` and re-running `parse_fx.py`:
  `rows=338,823  currencies=43  span=1999-01-04 .. 2026-09-02`,
  `sources={'ecb': 220484, 'ffill': 97323, 'peg': 10911, 'eur': 10104,
  'euro_conv': 1}`. That single `euro_conv` row is the locked HRK rate for
  2022-12-31 — one, as designed, and a cheap way to tell a correct FX build from
  a plausible-looking one.
- FX source: **ECB euro reference rates**, downloaded to `data/fx/` (files are gesmes
  XML, not CSV): `eurofxref-hist.xml` (full history, 7058 business days 1999-01-04 →
  2026-07-28, 41 currencies) and `eurofxref-daily.xml` (ongoing daily). Rate = units of
  currency per 1 EUR, so `price_eur = price_local / rate`. Free, reuse-with-attribution.
  Sandbox can't reach ecb.europa.eu, so download manually.
- ECB rates are daily, business days only. Apply the rate of the delivery day (UTC date
  of `delivery_ts`), forward-filled over weekends/TARGET holidays. One documented assumption.
- **UAH (Ukraine) — NOT in ECB.** Use the National Bank of Ukraine official rate (the
  ECB-equivalent for UAH). Download URL (change valcode=eur for EUR; dates yyyymmdd):
  `https://bank.gov.ua/NBU_Exchange/exchange_site?start=yyyymmdd&end=yyyymmdd&valcode=eur`
  Saved as `data/fx/nbu_fx_uah.xml`, parsed by `src/parse_fx_nbu.py` -> `fx_uah.feather`
  (same schema; concat onto fx for the UA run). Ukraine is NOT in daily monitoring — one-off
  history only. Caveat: NBU rate is the OFFICIAL rate (USD-peg 2022..Oct-2023, managed float
  since) and UAH devalued hard, so EUR-converted UA numbers mix market vol with FX depreciation.
- Currencies actually seen in IM (2020_01 sample): BAM, CZK, EUR, GBP, HRK, HUF, PLN, RON
  (full list from `currencies_seen` once IM history is built). HRK ends when Croatia
  joined the euro (2023). **Pegged currencies NOT in ECB**: BAM and BGN are fixed to EUR
  by currency board (1 EUR = 1.95583); the FX layer must supply these as constants, not
  from ECB. `parse_fx.py` (gesmes XML -> long table rate_date/currency/rate + pegs) is
  the next FX step, not yet written.

## The source: see docs/ENTSOE.md

Everything about ENTSO-E now lives in its own file: licensing, the API's
structure facts, how and when the platform actually publishes, the catalogue of
data gaps, and the correspondence with the operators.

The split is deliberate. **This document holds OUR decisions — things we chose
and can change by argument. `ENTSOE.md` holds facts about the SOURCE — things we
can only observe, and which get revised by evidence, usually arriving as an
email.** Mixing them made it hard to tell which of our "rules" were actually
constraints imposed from outside.

One correction that came from there and matters here: **DA is not 15-minute
everywhere.** HANDOFF used to state that every European zone went native 15-min
on 2025-10-01. Albania's TSO told us directly that it has not implemented
15-minute products at all. The code never relied on the claim — resolution is
read per Period and upsampled — but do not reintroduce the assumption.

## Where the code is

`src/`, and `docs/MAP.md` describes it file by file — that listing used to be
repeated here and went stale twice, so it now lives in one place.

Two GitHub repositories: **`powertradinglab-benchmarks`** (private today, to be
opened) and **`powertradinglab-site`** (public, the site and its data). A third,
**`powertradinglab-backup`**, is private for ever and holds the snapshot. The
older names `trading-lab-benchmark-core` and `trading-lab-benchmark-public`
appear in commits before 2026-09-26 and mean the first two.

Python 3.13, uv, ruff, pytest. Developed on an M4 MacBook Air, run on Ubuntu.

## Benchmark definitions (DA↔IM)

Everything is measured PER 1 MW of trading capacity — the benchmark is an efficiency
yardstick, NOT an absolute market size. A real algo with mandate M MW and profit P is
judged as P/M against these per-MW numbers (if P/M is below the passive ideal, the
clever algo lost to the lazy one). Do NOT scale by consumption — that gives huge,
uninformative figures. Consumption (ActualLoad) is only for ZONE SELECTION, not for the
metric.

Scope: DA↔IM ONLY. IM is the terminal (real-time) price and DA the anchor, so DA-IM is
the OUTER envelope of short-term trading; intermediate auctions (IDA) sit inside it and
add little except on anomaly days. (IDA data is also almost absent in File Library — only
ES 2026 — so DA-IM is the only thing computable broadly.)

Per 15-min PTU, given DA price and the two IM prices:

    buy  = max(price_im_pos, price_im_neg)   # price to buy in IM (worse side)
    sell = min(price_im_pos, price_im_neg)    # price to sell in IM (worse side)

    # PHASE 1: four benchmarks, all per 1 MW, no abstention/clip. * 0.25 = MWh per PTU.
    # NAMED BY THE TRADER'S ACTION on DA (opening the position is the decision the trader/algo
    # makes; IM just settles afterwards, no trader involvement). So the name = the DA side.
    always_buy  = (sell - price_da) * 0.25    # decision = BUY on DA; IM settles by selling
    always_sell = (price_da - buy) * 0.25     # decision = SELL on DA; IM settles by buying
    ideal       = max(always_buy, always_sell)  # oracle: best per-PTU direction (may be <0 in dual)
    devil       = min(always_buy, always_sell)  # oracle: worst per-PTU direction

- `* 0.25`: 1 MW over a 15-min PTU delivers 0.25 MWh (price is EUR/MWh).
- NO clip in phase 1. Clipping `max(0, ...)` would add a 3rd action ("don't trade") =
  a SEPARATE, smarter benchmark (abstention) — a later family member, not the base. Without
  clip, `ideal` can go NEGATIVE in dual zones when DA sits inside [sell, buy]: even perfect
  direction loses to the dual-pricing penalty band. That negative is informative, keep it.
- always_buy / always_sell: no foresight, always the same DA action. Their SIGN over a period
  = the market's structural bias. always_buy > 0 => IM > DA (deficit-prone / expensive IM);
  always_sell > 0 => IM < DA (surplus-prone / cheap IM). `ideal = max`, `devil = min` per PTU.
- **Action encoding (numeric, not words):** the DA decision is a number, not a string —
  `buy = +1`, `sell = -1`, and (once added) `idle = 0`. When the complex math arrives it
  outputs a probability/score interpreted on the SAME continuous scale `[-1, +1]` (e.g. +0.7
  = lean buy, -0.3 = weak sell), so a signal and a hard action share one representation and
  no code branches on strings.
- 5th benchmark `stat_action` (causal, "simple but not dumb"): hourly trailing-bias. Per
  hour-of-day (UTC), compare trailing N-day mean of always_buy vs always_sell -> pick the DA
  side; realised pnl = the chosen side's hourly pnl. Causal via `shift(2)` (48h: decide for
  D on D-1, freshest complete fact is D-2) — the phase-1 shortcut for the canonical
  `knownby_ts < current_ts` as-of rule. First look: `stat_action` is negative in absolute
  terms (naive momentum can't beat the dual penalty) but usually beats the best FIXED single
  side, i.e. it harvests some persistent time-of-day bias.
- min/max makes it label-agnostic: no need to resolve pos/neg ↔ long/short (each TSO defines
  short/long from its own side). max=buy, min=sell regardless. (Irina's insight, from pos>neg
  in some zones, pos<neg in others.) So the pos/neg↔long/short cross-check is moot.
- `0` in an IM price is a REAL €0/MWh (NL trading experience — by IM close all positions
  balance 100%, there is always a settlement price). No zero-handling.
  **But that rule is about a PRICE that happens to be zero, and it has a limit:**
  one leg sitting at exactly 0.00 for every quarter-hour of a month, while the
  other runs at 150–280, is an unused column, not a price. Confirmed for all
  Italian zones since 2022-04 and for SK since 2024-07 (see `ENTSOE.md`). Those
  zones are excluded from the report; NL is unaffected (both legs always
  populated).
- Single-price zones (pos==neg): always_sell == -always_buy and devil == -ideal (symmetric).
  Dual zones (NL, FR, HU, CZ, ES, PT, CH, all Italy, SI, SK, AL, MK — and RO until
  2026-06-30): asymmetric; the
  asymmetry itself distinguishes single vs dual pricing empirically (25 single / 19 dual seen).

Interpretation — this is a MARKET-ATTRACTIVENESS map for a BRP (which zones to add/drop):
- `ideal`/`devil` per (area, year) = the envelope of extractable value per 1 MW = how "fat"
  a market is, and (across years) how PERSISTENT the fat is.
- Findings (yearly.csv, no-clip): 2022 was a very fat year across ALL zones (mean ideal x2.4
  vs 2020) then decayed — but at different rates: HU/RO retained ~70% of their 2022 peak,
  NL/BE/CZ fell to ~40%. Level AND persistence matter (a persistence metric is planned:
  e.g. years a zone holds >= X% of its peak). BE's collapse matches Irina's lived experience.
- Richness ranking (mean ideal EUR/MW/yr): RO >> HU > Baltics(LV/EE/LT) > CZ > BE > AT > SK
  > DE_LU > NL. NL (the famous one) is a solid mid-pack; RO is the persistent leader.
- CZ case: fat in 2022 (~1.46M) when a firm planned to add it, deflated to mid-pack by 2025
  (~577k, rank 9) — a decision right in the moment that aged badly; the persistence metric
  would have flagged it. Good teaching case.
- Open hypothesis (Irina): there may be a FLOOR of fatness below which no zone drops — to be
  seen over more years.
- Zone-selection plan: start with NL (home market, all nuances known), then add contrasting
  "странные" zones — ES (structurally unprofitable, `ideal` <= 0) and RO (volatility leader).
  Target set ~10 zones, balanced 5 dual / 5 single. Go one zone at a time, digging into each
  zone's quirks (like NL zeros). Don't try to cover all at once.

ANOMALIES to eyeball before trusting (dual zones with `ideal` <= 0 for whole years): CH
(negative every year, huge devil), PT, ES, all Italy. Either a genuinely punishing dual
design or their pos/neg columns encode something else (e.g. a scarcity component) — check
the raw IM for CH and Italy. RO magnitude: check RON outliers.

## Zones excluded from the report, and why

Stated openly in the report rather than quietly dropped. Every exclusion has a
reason, and "needs individual work" is an honest reason — chasing every zone's
quirks would be a year of archaeology and no report.

- **All Italian zones** (IT-NORTH, IT-CNORTH, IT-CSOUTH, IT-SOUTH, IT-Sicily,
  IT-Sardinia, IT-Calabria) — the Negative leg is published as zero since
  2022-04, so the DA-IM envelope cannot be computed as it stands. Individual
  work required; a ticket is open.
- **GB** — only one year available.
- **MK** — only 2025-2026 available.
- Plus the structural exclusions already listed under "Tradeable universe":
  virtual/flowgate zones, zones with no A85 at all, and IM-only zones.

SK is borderline for the same reason as Italy and its classification is suspect;
decide once the ticket is answered.

## Coverage: annual sums are NOT comparable across zones

ENTSO-E did not start receiving imbalance prices from every zone at once, and
several zones have long gaps since. The catalogue of which zones and when is in
`ENTSOE.md`; the rule below is ours.

NO1's first imbalance timestamp is **2021-10-31**, so its "2021" is two months
while another zone's 2021 is twelve. In a report that gap does not read as
missing data — it reads as "there is nothing to trade in NO1", which is false.
Day-ahead has no such problem: it was organised centrally from the start.

So the reporting basis is the MONTH, not the year:

- a year is shown as an annual sum **only if all twelve months are usable**;
- otherwise the monthly average is shown, **with the months it covers named**;
- a partial year is never silently scaled up to twelve;
- cross-zone comparison uses a common set of months.

A month is USABLE when both legs are complete — the benchmark is a DA-IM spread
and one leg computes nothing. `modelling/coverage.py` builds the table
(`modelling/coverage.csv`, one row per zone and month). Completeness is counted
in UTC months on purpose: a UTC month holds exactly `days x 96` intervals, always,
because the 92/100 daylight-saving wrinkle only exists once days are anchored to
local midnight. That makes the expected count exact for every zone without a
timezone table for forty countries, and shifting a month boundary by an hour
cannot change whether the data exists.

Open question, worth measuring before trusting short spans: Irina's view is that
a two- or three-month average is still usable as long as it is flagged, and that
the seasonality objection (a winter-only average reading high) is not obvious —
NO1's first months were the thin covid period. That is testable on the zones with
complete coverage: measure how far a single month can sit from its own year's
average, and the answer says how much weight a two-month figure can carry.

## Why a year is fat: `ideal` decomposes into three drivers

Found 2026-08-28, verified on real data (agreement to 5e-14, i.e. exact).

Per PTU, with `mid = (buy + sell)/2`, `band = buy − sell`, `gap = mid − da`:

    ideal =  ( |gap| − band/2 ) · 0.25
    devil =  ( −|gap| − band/2 ) · 0.25

So extractable value has exactly three drivers, and they are separable:

1. **price level** — scales `|gap|` proportionally;
2. **relative mispricing** `|gap| / level` — how badly day-ahead predicts
   imbalance, independent of what electricity costs;
3. **band width** — a pure subtraction, zero in single-price zones.

This answers the question the volatility ratio was reaching for, and it does not
explode: the denominator is the DA price level, comfortably positive, rather than
the mean imbalance price, which crosses zero (see the abandoned `std/mean`).

**June, NL and DE_LU, indicative only — the full history is not yet run:**

| zone | year | ideal | \|gap\| | band/2 | DA level | \|gap\|/level |
|---|---|---|---|---|---|---|
| NL | 2022 | 77 460 | 113.79 | 6.21 | 210.70 | **0.540** |
| NL | 2024 | 56 008 | 97.87 | **20.09** | 68.06 | **1.438** |
| DE_LU | 2022 | 72 377 | 139.59 | 0 | 186.71 | 0.748 |
| DE_LU | 2024 | **101 479** | 115.74 | 0 | 72.24 | **1.602** |

Read it this way:

- **2022 was a LEVEL effect.** NL's relative mispricing was at its LOWEST that
  year (0.54). The market was fat because everything was multiplied by three,
  not because forecasting got harder.
- **2024 was STRUCTURAL.** Prices had fallen by two thirds while `|gap|` barely
  moved, so the ratio hit its maximum. DE_LU's peak is **2024, not 2022** — the
  highest `ideal` in the sample at a third of 2022's price level. Consistent with
  the renewables hypothesis: more wind and solar, worse day-ahead prediction,
  regardless of price.
- **That is why zones split into a 2022 group and a 2025 group with few in
  between** — two different mechanisms peaking at different times, and in each
  zone one of them dominates.
- **NL's band/2 quadrupled**, 5.00 → 20.09. It pays a tax DE_LU does not, which
  is why Germany's `ideal` is higher on a similar `|gap|`.

## Market regime transitions (dual <-> single IM pricing) & alpha decay

Measured from IM data: per (area, year), the share of PTUs with `pos != neg` (dual share).
S = single (<5%), D = dual (>40%), m = transition. Regimes are NOT static — zones switch:

**WARNING (2026-08-28): this table is derived from the share of PTUs with
`pos != neg`, and a leg published as ZERO reads as a second price. The SK row is
therefore suspect — its "dual" begins in the very month its Negative leg starts
filling with zeros (2024-07). Italy would be misclassified the same way and is
excluded. AL was checked and is genuinely dual (its Negative leg is populated,
1–23% zeros). The other rows are unaffected: no other zone has a zero leg. See
`ENTSOE.md`; re-derive this table once the tickets are answered.**

      2020 2021 2022 2023 2024 2025 2026
    AL  S    D    D    D    D    D    D      single -> dual (2021), verified
    SK  S    S    S    S    D    D    D      SUSPECT — zero leg from 2024-07
    HU  D    m    S    S    S    S    m      dual -> single (2022); faint dual creep-back in 2026
    SI  D    D    D    S    S    S    S      dual -> single (2023)
    CZ  D    D    D    D    m    S    S      dual -> single (2025)
    CH  D    D    D    D    D    D    S      dual -> single (2026)
    RO  D    D    D    D    D    D    m      dual -> single, from 2026-07-01

- dual -> single: HU, SI, CZ, CH, RO. single -> dual: AL, SK. So MORE zones move D->S.
- Owner's read: single is friendlier to speculation (no dual penalty band, symmetric DA-IM
  spread), so D->S may draw in speculators and grow imbalance-market volume. HYPOTHESIS to
  test with regulation-volume data (idea): download up/down balancing volumes, normalise by
  actual load, and relate the regulation-volume share to the pricing regime, per zone/year.
- ALPHA DECAY (the product's whole point): markets are thinning fast. NL/BE/FR ideal fell to
  ~40% of the 2022 peak by 2025; RO's easy one-sided bias captured ~99% of ideal in 2020 and
  ~1% by 2025. Owner's lived experience: backtests on BE/FR/NL 2021-2023, traded 2024-2026 —
  the market thinned so hard the backtests were just catching STALE alpha with less and less
  ahead. This is exactly what the benchmark makes visible: WHEN a market was fat, so a trader
  can tell whether their backtest window still applies. Algo trading in these conditions is
  often a 1-3 month opportunity, not a durable edge — and many traders hit this unknowingly.

### RO went single-price on 2026-07-01

Established for the report and recorded here on 2026-09-23, because the live
path and the report must say the same thing about the same zone. RO was
dual-priced from 2020 through June 2026 and publishes ONE imbalance price from
1 July 2026.

What it changes for the benchmark, mechanically: the penalty band disappears, so
`always_sell == -always_buy` and `devil == -ideal`, and the decomposition's
`band/2` term goes to zero. What it changes for the reading: RO was already the
richest zone by `ideal` and the most persistent (about 70% of its 2022 peak
retained, against 40% for NL and BE), and single pricing removes the one thing
that was taxing every trade in it. That is the owner's D->S hypothesis —
single is friendlier to speculation — arriving in the zone where it is easiest
to see.

The 2026 column of the table above is therefore `m` for RO: dual for half the
year, single for the rest.

## Tradeable universe & excluded area codes (DA-IM)

Root cause of DA/IM area mismatches: DA is published per **bidding zone (BZN)**, IM per
**scheduling / imbalance area (SCA / IPA)** — different taxonomies. Most countries coincide
(NL, FR, …), some don't. Tradeable universe = areas present in BOTH DA and IM over the full
history (~40 zones). Excluded codes, by reason:

- **Virtual / interconnector "сечение" (flowgate) zones** — a DA coupling price but NO
  imbalance area (a nodal element inside the EU zonal model; imbalance settles in the parent
  zone): `NO2NSL`, `IT-SACOAC`, `IT-SACODC`, `IT-Rossano`.
- **No A85 imbalance published to ENTSO-E**: `BG` (Bulgaria), `XK` (Kosovo), `IE_SEM`
  (Ireland/NI SEM — own imbalance via SEMO, not in ENTSO-E A85).
- **IM-only / no DA (islanded, not in SDAC day-ahead)**: `CY` (Cyprus).
- **Junk**: empty-string area code `''` in DA (drop).

NOT excluded, just handled:
- **`DE_LU` (DA) == `DE` (IM)** — same market (Germany-Luxembourg), different label. Alias,
  do NOT drop. **DOUBLE alias — both codes changed at the 2023 relabel**, so map BOTH:
  `area`: `DE -> DE_LU`, AND `area_eic`: `10Y1001A1001A83F -> 10Y1001A1001A82H`. Since we
  de-dup / join on the canonical `area_eic`, replacing only the readable `area` leaves
  2023+ German IM (currency, prices) hanging on the un-aliased EIC -> currency shows NaN and
  those years drop. Apply the EIC alias too and DE_LU computes across all years.
- **`LT`, `ME`** and similar: IM present in some periods, missing in others (e.g. 2026_06) —
  temporal gaps, not exclusions. Build the universe over full history; let per-period gaps be
  NaN / handled by as-of, don't drop the zone.

## The early plan, and the four things that survive it

The build lists that used to stand here — ingest, parsers, the File Library
backfill, the fifth benchmark, the week-by-week cadence of the first NL loop —
are all done, and what they produced is in the code and in the sections below.
They are in git history for anyone who wants to see the order things happened in.
Four items from that period are still live and would have been lost with them:

- **Positive == A04/long, Negative == A05/short.** Settled row for row on NL
  2026-07-25 (a saved API zip against the monthly extract), 40 of 96 PTU
  dual-priced, all exact. This mattered not for the metric — min/max would hide a
  swap for ever, since no published number would move — but for the DATA: once
  the API feeds the same store as the File Library, a wrong mapping mirrors the
  two columns in every live row. An earlier guess in `parse_filelibrary` that the
  names were flipped came from the ORDER of the two prices, which varies by PTU
  and says nothing about the labels.
- **The HRK tail.** `parse_fx.py` `_EURO_LEGACY` fills HRK on 2022-12-31 with the
  locked rate 7.53450 (source `euro_conv`): the ECB stops publishing HRK on
  2022-12-30 and Croatia joined the euro on 2023-01-01. It generalises to any
  other retired currency.
- **ENTSO-E maintenance still reads as a failure, deliberately.** A 503 whose
  body says `Scheduled maintenance is currently underway` burns all four retries
  and leaves four ERROR lines for something that is neither our fault nor a
  problem — the three-day poll window collects the day tomorrow at no cost. The
  shape of the fix is known and is the same move as `Acknowledgement` code 999:
  recognise the body, log one line, skip the retries. Not written yet, on the
  owner's call, because two outages (2026-08-30 and 08-31) are not enough history
  to say how the platform behaves, and a rule keyed to the wrong pattern is worse
  than the twenty minutes of retries it would save. The first reading — "a Sunday
  maintenance window" — was already wrong by the next morning, which is the
  argument for waiting made concrete.
- **Deferred by choice, not forgotten:** the remaining zones, a neural-net / DRL
  member of the benchmark family, and a paid Python-API tier.

### Scheduling — launchd, TWO cadences (not one)

`uv run python scripts/make_launchd.py [--install]` writes and loads two jobs;
`scripts/run.sh {poll|daily}` is what they call.

- **ONE poll a day, on the decision itself** (since 2026-08-12). It began as five
  a morning to MEASURE when imbalance appears; five days running it was complete
  by 05:30, long before the decision, so the question is answered and the extra
  polls were only costing raw files.
  What the five also provided by accident was redundancy, and that mattered: in
  the first week, a source failure landed on the 09:30 slot itself (2026-08-07,
  both documents, DNS) and the forecast ran on the previous day's data. So the
  redundancy is now deliberate instead of incidental — `retry_attempts` (4, five
  minutes apart) re-polls until the poll log shows both documents fetched, and
  still finishes ahead of the 10:00 UTC summer gate. A failed fetch does not
  raise, so the retry inspects the poll log rather than catching an exception.
  With no poll time left outside the decision, `make_launchd.py` creates no
  separate poll job — and actively REMOVES a previously installed one, because a
  plist left behind keeps firing on the old schedule and nothing says so.
- Computing runs ONCE a day at `run_time_utc`: NL publishes imbalance as a batch
  for the completed day and nothing intraday, so there is no new information to
  react to hour by hour. One recompute per day, not 24.
- **Separate jobs so the decision run is an ordered chain**: update -> forecast
  -> score. Scheduling a poll and a compute at the same minute as independent
  jobs would race, and the compute could read the store before the poll wrote to
  it.
- A failed poll does NOT abort the forecast. Under the as-of rule a forecast on
  a slightly older window is still correct and says so in `data_through`, while
  skipping it would leave a hole in a daily series. Failures are loud in the log.
- **launchd's StartCalendarInterval is LOCAL time, our schedule is UTC.** Hence
  a generator rather than hand-written plists: the conversion happens once, is
  printed for checking, and is recorded as a comment inside each plist. Yerevan
  (UTC+4) has no DST so the mapping is stable; re-run and reload after any
  timezone change, and mind that the decision run must stay ahead of the 12:00
  CET gate.
- Missed runs are survivable by construction: each poll re-requests the whole
  window and catches up, and `knownby_ts` records the REAL fetch instant, so a
  late run makes the measurement coarser rather than wrong.
- `--install` VERIFIES the end state against `launchctl list` instead of trusting
  the commands it just ran, and exits non-zero on a mismatch. Reason: `launchctl
  unload` returns non-zero for ordinary reasons ("not loaded"), so its exit code
  cannot be read strictly — which means a failed removal could leave a job firing
  on an old schedule with no plist on disk to show for it. Nothing would report
  that. It would surface days later as extra runs in the log, if anyone noticed.
- Logs: `logs/launchd_{poll,daily}.log` for the chain, `logs/workflow.log` for
  the steps themselves.

### Operating the scheduled jobs (cheat sheet)

Three jobs: `com.tradinglab.daily` (09:40 UTC), `com.tradinglab.catchup`
(14:00 UTC) and `com.tradinglab.monthly` (08:00 UTC on the 20th). Labels carry
no zone since 2026-09-20 — one process runs every zone. Everything below is
run from the repo root; `$LA` is `~/Library/LaunchAgents/`.

```bash
# WHAT IS RUNNING
launchctl list | grep tradinglab     # the jobs + last exit code (0 = fine)
tail -f logs/launchd_daily.log       # follow the chain; Ctrl+C stops watching,
                                     # NOT the job
grep -n "===" logs/launchd_daily.log | tail -4   # the last run's boundaries

# RUN ONCE, NOW (does not disturb the schedule)
launchctl start com.tradinglab.daily

# PAUSE — the -w writes "disabled" into launchd's own database, which is what
#         makes the pause survive a reboot and a re-login.
for j in daily catchup monthly; do launchctl unload -w $LA/com.tradinglab.$j.plist; done

# RESUME — and it MUST be load -w. The -w above left each label marked
#          disabled, and a plain `load` refuses a disabled job with
#          "Load failed: 5: Input/output error".
for j in daily catchup monthly; do launchctl load -w $LA/com.tradinglab.$j.plist; done
launchctl list | grep tradinglab     # three labels, or it did not work

# INSTALL / REINSTALL — after changing TIMES or TIMEZONE, not after a pause
uv run python scripts/make_launchd.py            # dry run: prints the schedule
uv run python scripts/make_launchd.py --install  # writes the plists and loads

# CHECK WHAT launchd THINKS IS DISABLED
launchctl print-disabled gui/$(id -u) | grep tradinglab

# REMOVE COMPLETELY
for j in daily catchup monthly; do launchctl unload -w $LA/com.tradinglab.$j.plist; done
rm $LA/com.tradinglab.*.plist
```

```bash
# BEFORE CHANGING CODE THAT THE SCHEDULE RUNS
# 1. pause (all three, -w)       2. edit, run the tests
# 3. resume with load -w         4. launchctl list | grep tradinglab
```

**Learned 2026-09-22: `--install` does not undo a pause.** This sheet used to
say it did ("pause, edit, `make_launchd.py --install` brings it back"). It
never did; it had simply never been tried on a label that had been paused. On
2026-09-20 it worked by accident — the NEW labels had never been disabled, only
the old `nl.*` ones. Two days later the same labels were paused with
`unload -w`, and `--install`, which loads with a plain `load`, was refused on
all three with `Load failed: 5: Input/output error`. Diagnosis in one line: a
`load -w` by hand worked at once.

Two things made it cheap. The verification at the end of `--install` checks
`launchctl list` instead of trusting the commands, and it said `NOT LOADED` for
all three and exited non-zero — while the lines above it still printed
"installed and loaded", because **`launchctl load` exits 0 even when it
refuses**. That is the reason the verification exists, and here is the case
that proves it. A schedule that silently did not come back would have cost a
forecast the next morning, and a lost forecast is not recoverable.

Fixed the same day in `make_launchd.py`: it loads with `load -w`, and prints
"load requested" rather than "loaded", because only `_verify` knows. Resuming
after a pause by hand still works and is the shorter command — use the loop
above; `--install` is for when the TIMES changed.

Notes worth remembering:

- **Pause the job before a refactor.** On 2026-08-28 the zone registry was
  rewritten twenty minutes before a scheduled run — `period`'s signatures, the
  EIC constants and the raw filenames all changing at once. It survived only
  because that day's run had already been missed for an unrelated reason. Had it
  fired mid-edit, it would have failed on a half-changed tree, and we would have
  been debugging two problems at once with no way to tell them apart. The system
  runs itself now; that is exactly what makes editing it in place a hazard.
- **A timezone change does not land instantly, and the plist is not where to
  look.** After the move to Yerevan (+04) the daily run fired at 10:30 UTC on
  27, 28 and 29 August instead of 09:30, then corrected itself on the 30th with
  no intervention. The plist was right the whole time — `Hour 13, Minute 30`,
  which is 09:30 UTC at +04 but 10:30 UTC at +03. `make_launchd.py` read the new
  zone when it generated the file; the OS was still serving the old one to
  launchd, and the two agreed only a couple of days later. The lesson for
  diagnosis: `date` answers "what is the zone NOW", which is the wrong question
  once the discrepancy has healed — the decisive evidence is the timestamp of
  the next scheduled run, so wait for it rather than reasoning from the current
  zone. (Two wrong diagnoses were offered before that, both stated too
  confidently: a stale loaded plist, and the timezone theory declared dead on
  the strength of a `date` taken after the fact.)
- **A reinstall does not backfill the slot it just missed.** Re-registering the
  schedule after the day's time has passed means nothing runs until tomorrow —
  launchd catches up runs missed while ASLEEP, not runs that were not yet in its
  schedule. After changing times (a move, a timezone change), run
  `launchctl start com.tradinglab.daily` once by hand.
- Unloading does NOT kill a run already in progress; it finishes.
- The terminal is irrelevant — the jobs live in launchd, so closing the window
  (or logging out) changes nothing.
- A sleeping Mac does not wake for a job. launchd runs the missed one ONCE on
  wake, not once per missed slot. Nothing is lost: each poll re-requests the
  whole window, and `knownby_ts` records the real fetch instant, so a late run
  makes the measurement coarser rather than wrong. `sudo pmset repeat
  wakeorpoweron MTWRFSU 12:25:00` (LOCAL time) wakes the machine if the daily
  run ever needs guaranteeing.
- **After moving back to Yerevan, re-run `--install`.** The plists hold LOCAL
  times computed from whatever timezone the machine had at generation. Moving
  MSK (UTC+3) -> Yerevan (UTC+4) without regenerating shifts the decision run
  from 09:30 to 08:30 UTC. Still before the auction gate, so not fatal — but the
  signal window gets a day staler more often. The drift is visible in the data:
  `knownby_ts` in `forecasts.parquet` would read 08:30 instead of 09:30.

### What the first publication failure taught (2026-08-08/09)

`<publisher>` was added AFTER the first files had been published, and the schema
version was not raised. Every already-published file then rendered differently,
the immutability check refused to overwrite them — correctly — and the run died.
Three separate lessons, only the first of which was the original mistake:

1. **Adding an element is a schema bump.** The rule was already written down the
   day before. Writing a rule down does not make it fire; the check did.
2. **A refusal must not have unlimited blast radius.** One frozen file from July
   stopped the publication of everything else, including days that had no
   conflict at all. Two daily runs produced no files. Now a conflict is logged,
   the file is skipped, the rest are published, and the exit code carries the
   bad news. Refusing to do unrelated work is a worse failure than the conflict.
3. **An unhandled traceback is invisible where it matters.** It went to stdout,
   which under launchd is a different file, so `workflow.log` showed nothing and
   it looked as though the step had never run. `main()` now logs through the
   logger before re-raising. The same one-liner belongs in the other entry
   points and is not there yet.

### Versioning of published files — TWO numbers, raised by hand

`settings.json -> publication`, read by `config.versions()`. Both start at **1**:
nothing has been published yet, so any other number would be an invention.

| number | describes | bump when |
|---|---|---|
| `schema_version` | the SHAPE of the file | a parser written for the previous version could break — an element renamed, removed, moved, **or added** |
| `methodology_version` | the NUMBERS | the same input could now produce a different output |

The one-line test for each: **methodology up when the old input gives a new
output; schema up when the old parser gives an error.**

They are separate because they have different readers. Whoever wrote a parser
cares about the first; whoever compares March against September cares about the
second. A single combined number would force a recalculation notice over a
cosmetic change to the markup.

The case that will actually come up (Irina's, and she is right): the current
benchmarks are unlikely to change, but their NUMBER will grow. Adding a sixth
family member is a **schema** bump and NOT a methodology bump — every number
already published stays bit-identical, only the set of elements grows. Which is
exactly the distinction that a single version could not express.

Design consequence for the published XML, to settle when it is written: if the
family is expected to grow, the benchmarks should be a LIST of named entries
rather than a fixed set of elements. Then a new member is additive and old
readers keep working.

Because the bumps are manual — and one will be forgotten eventually — every
published file also carries the parameters that actually drive the numbers
(`config.publication_parameters()`: n_days, final_day_of_month, run_time_utc,
causality). The version is for quick comparison; the parameters are the proof.

Changelog — keep it here, in words, not in the json:

- **schema 5** (2026-09-18) — a score file may carry NO action. The `action`
  attribute and `trailing_bias_value` are then absent — not zero, not empty —
  and `<no_action>` says why: the refusal's own reason, or
  `no_forecast_issued` when the run never produced a forecast row for that day
  at all. Methodology stayed at 2, on the owner's call: no already-published
  number moves, and the four market values are computed by exactly the method
  already described. The argument the other way is real and was heard — where
  there used to be no output there is one now — but what changed is WHICH days
  get looked at, not how any number is made.
- **schema 4** (2026-09-14) — the five values got their public names,
  `n_days_default` became `n_days_trailing_bias_default`, `<action_codes>`
  added. Numbers unchanged. See the schema 4 section.
- **schema 3 / methodology 2** (2026-08-31) — the forecast may refuse an
  incomplete input day and publish `<no_forecast>` instead. The document gains
  a shape an older parser would not expect, and the same input can now produce
  a documented refusal where it used to produce an action. See the input-gate
  section.
- **schema 2** (2026-08-10) — added `<publisher>`. Numbers unchanged, so
  methodology stayed at 1 — the case that justified having two numbers in the
  first place. The whole archive was re-rendered with `--force`; nothing had
  left the machine yet, so this was the last free moment to do it.
- **schema 1** — first published layout (see the publication section).
- **methodology 1** — phase-1 family: `always_buy`, `always_sell`, `ideal`,
  `devil` (per 1 MW, DA-IM, no clip) plus `stat_action` (hourly trailing bias,
  n_days from settings); causality by `as_of`; a delivery day scored twice.

### A hand-supplied `current_ts` is a SIMULATION and is not stored

`workflow_compute forecast|score <timestamp>` computes and logs, but writes
nothing. Only a run with no timestamp (i.e. `current_ts = now`) persists.

Why: `knownby_ts` in our own tables IS `current_ts`. A stored row from a
back-dated run therefore claims we knew something at a moment when this code did
not exist — and that claim gets published. It did: `outputs/nl/2026/07/
score_NL_2026-07-21_20260725T093000Z.xml`, dated 25 July, was produced by a
command run on 5 August. That file is being kept deliberately (it harms nothing,
and analysis starts from 1 August anyway), but the door is now shut.

Looking at the past WITHOUT writing is what `modelling/validate_as_of.py` is for.

### Publisher identity is separate from format

The root element and element names are the FORMAT: frozen the moment anything is
published, and renaming one breaks every parser. A project name and a domain are
not that kind of thing — they get rebranded and they move. So identity sits in
`<publisher name="..." url="..."/>`, whose content can change freely without a
schema bump. Edit `publication.publisher_name` / `publisher_url` in settings.

### Four decimals in the published files, not two

Tempting to round to cents — the prices are in cents, after all. But we do not
publish prices: we publish price × 0.25 MWh (a quarter hour at 1 MW), so one
cent of price becomes 0.0025. Values like `17.1875` are exactly `68.75 × 0.25`,
not floating-point dust. Measured on the August files, **74 % of values need
three or four decimals**.

So four decimals is the EXACT representation, and rounding would discard real
information — and break the check that totals equal the sum of the points (the
drift is a few cents a day, and it is what an independent hand-verification
would trip over first).

Round for humans, on the site and in the report, where `−625.37` genuinely reads
better than `−625.3675`. Not in the file: scripts read it, extra precision costs
them nothing, and it cannot be recovered once dropped.

### A coin-flip benchmark: the mean needs no randomness

Worth recording before it gets built. The expected value of choosing a direction
at random is **exactly `(ideal + devil) / 2`** — no simulation required, because
`ideal` and `devil` are the max and min of the same two numbers. On NL 2026-08-06
that is −485.04, against `stat_action` −625.37: the signal did worse than a coin
that day (one day, no conclusion).

Randomness is only needed for the SPREAD around that mean, and the spread is the
interesting part: without it there is no way to say whether a strategy's result
differs from noise. So a Monte-Carlo member of the family would deliver a
confidence interval, not a reference point.

If it ever becomes a published benchmark: publish the analytic mean, or a drawn
series WITH ITS SEED recorded. An unseeded draw would make a frozen file stop
reproducing, which breaks the archive's only real promise.

### The monthly re-fetch — without it, `as-final` is a ceremony

The daily poll asks for a THREE-DAY window. A revision arriving weeks later would
therefore never be seen: we simply stop asking about July. The as-final pass on
the 20th would re-read the store, find the as-known values still sitting there,
and report "no revision" — not because nothing changed, but because nobody looked.

So on `final_day_of_month`, before the daily slot, a third job re-requests the
WHOLE previous month: `uv run python -m src.update --last-month`, scheduled at
`update.refetch_time_utc` (08:00, i.e. ahead of the 09:40 decision — the clock is
what guarantees the order, and `make_launchd.py` warns if the two get swapped).

The re-fetch day is DERIVED from `scoring.final_day_of_month`, not configured
separately: the re-fetch exists only to feed the final pass, so its date cannot
be allowed to drift away from that rule.

Nothing else was needed — `update --from/--to` was written so that "filling a
gap is the same command with a longer range", and this is that case. The
versioning then does the rest by itself: a changed value is a new row with
today's `knownby_ts`, the as-known snapshot stays beneath it, and `as_of` picks
the newer one. If nothing changed, no rows are written and the final pass repeats
the as-known numbers — which is now a genuine finding.

### A range longer than one request may cover (2026-09-16)

ENTSO-E capped API requests at 30 days on 2026-09-03 (see the bullet further
down). August is 31, so the as-final pass due 2026-09-20 would have been refused.

`update.split_range` now cuts ANY range into chunks of at most
`update.max_query_days` before it goes out, and each chunk is a request of its
own, retried on its own. Three things about it are deliberate:

- **It is not a branch on `--last-month`.** The cap is a property of the source,
  not of one caller. The monthly pass is the cheap casualty — miss it and it
  comes round in thirty days. The expensive one is the backfill after the next
  outage: forty days of hole, `--from/--to`, and the same wall at the moment the
  data is actually wanted. That is the case this protects.
- **The cut is EVEN, not "a full chunk and the remainder".** August becomes
  16 + 15, not 30 + 1. Both are legal under today's cap; only the even one is
  still legal if the cap tightens.
- **A chunk that fails does not stop the ones behind it.** The store takes only
  changes, so a partial pass is worth exactly the part that arrived.

The split is invisible in the store: chunks are disjoint and only changes are
written, so two half-month passes leave precisely what one whole-month pass would
have left. It IS visible in `polls.parquet` — two rows per document for a split
month instead of one. That table has always meant one row per request, and it
still does; anything counting passes by counting rows there would now be wrong.

**LIFTED on 2026-09-15**, announced 2026-09-14 — one day after this was built —
and `update.max_query_days` is **0** as of 2026-09-16. A year in one request is
allowed again. The splitter did not fire once in anger.

That is the intended end state, not a wasted afternoon. The reversal was one
number in one file: no code removed, no test deleted, nothing to remember. And
the reason it was built stands unchanged — the cap was never the point, the next
outage is. When it comes, set the number and the machinery is already there,
already tested, and does not have to be written by whoever is on the keyboard
that morning. This replaces the note of 2026-09-05 that said the fix was
deliberately not written; the owner's argument won it: *"мало ли у них еще всяких
ремонтов будет"*.

One lesson, paid for on the spot: the first version of
`test_the_cap_comes_from_settings_when_not_given` asserted "one day over the cap
gives two chunks". It went red within hours of the cap changing — it was testing
the VALUE in settings, not the wiring. It now asserts an equivalence instead. A
test that pins a live number fails on the day that number is finally right.

### outputs/status.xml — the single mutable file

Every other published file is frozen. This one is rewritten by every run, and it
sits at the ROOT of `outputs/`, outside the dated folders, so the boundary is
visible from the path alone. ONE file for all zones, not one per zone: a reader
asking "is this alive?" should not need a zone code first, and keeping the
mutable set at exactly one file is what stops the exception from becoming a
category.

It carries facts and no self-assessment — no `ok="true"`. A process cannot report
its own death, so a success flag is trustworthy precisely while nothing is wrong.
The file's own `generated_ts` is the heartbeat, and that cannot lie. Three cases
a reader can then separate without access to our logs:

- `generated_ts` old → the whole chain is down;
- `generated_ts` fresh, `im_through` stale → we are running, the source went quiet;
- both fresh but no new forecast → our side, but the signal did not form.

That distinction is the point: on the owner's previous project, working out
whether missing data was the source's fault or the pipeline's routinely cost more
than fixing it.

### The platform has a NEWS FEED — and it changes what an outage costs us

`https://external-api.tp.entsoe.eu/news/feed` — RSS 2.0, items carry `title`,
`description` (HTML) and `pubDate`, and nothing else: no status code, no
severity, no affected-service field. Urgency has to be read out of the prose.

Why it matters more than it looks. `status.xml` exists to answer ONE question —
whose fault is it — and today it answers only half: "we ran, the source went
quiet". The feed carries the other half. A line saying the platform itself
reports maintenance turns a silence into an explanation, without us guessing
from HTTP codes. That is the same job the maintenance-503 body was going to do,
except stated by the platform on purpose rather than inferred from an error page.

NOT built yet, deliberately (2026-09-05). It is a new external dependency in the
live path, and the failure mode is obvious: the feed can be down together with
the platform it describes, so nothing may ever depend on reaching it. Order
agreed with the owner: watch Monday and Tuesday through the migration first,
then RO, then learn to read the feed. One source of change at a time.

**What the feed already told us that the ticket reply did not** (read 2026-09-05):

- **A 30-day query limit is in force.** *"The Transparency Platform Web API is
  available again. As part of the ongoing stabilisation activities, a temporary
  limitation applies, and API requests covering periods longer than 30 days are
  currently not supported."* (2026-09-03.) The daily three-day poll is
  unaffected. **`update --last-month` was NOT**: it requests a whole calendar
  month, and August is 31 days — over the limit, so the as-final pass due
  **2026-09-20** would have been refused. Splitting was BUILT on 2026-09-16 (see
  "A range longer than one request may cover" above) and the cap was **LIFTED on
  2026-09-15**, so it never fired. `update.max_query_days` is 0; the month goes
  out whole again.

- **The platform was declared stabilised on 2026-09-14.** The publication backlog
  and the API performance problems are reported resolved, API limits lifted
  15/09 ("1 year of data with a single request"), website export limits 16/09.
  Subscription messages may still lag. This closes the incident that began with
  the rolled-back migration of 09-02: the four-day outage, the five manual
  backfills, the six refused forecasts and the permanently missing DA for
  delivery day 09-13 all belong to it.
- **The migration of 02/09 was ROLLED BACK** (2026-09-02), which is what the
  four-day outage actually was. Rescheduled to Monday 2026-09-07 16:00 CEST,
  up to six hours — 14:00-20:00 UTC, comfortably after our 09:30 UTC run. Public
  IP addresses AND certificates change with it: IPs are transparent to a client
  resolving by hostname, but a `CERTIFICATE_VERIFY_FAILED` on the Tuesday would
  be that, not us, and is cured by refreshing `certifi`, not by touching code.
  The imbalance batch for delivery day 09-07 is published around 05:30 UTC on
  09-08, i.e. right after the window closes — the likeliest day for the gate to
  refuse, and refusing would be correct.
- **Swissgrid stopped delivering data on 2026-09-02 08:00 CEST** and everything
  scheduled since then was affected. CH is a zone in the yearly table (one of the
  two "strange" ones with ES). The report snapshot is cut at 2026-08-31, so it
  should be clear — worth checking rather than assuming.

Also in force: temporary restrictions on LARGE data exports through both the GUI
and the Web API, until after the migration. Our polls are far too small to
notice; the full-history bundles in `data/archive/` are exactly what that
restriction is about, so a re-download waits until after 09-07.

### The archive comes from ONE bundle per product now (2026-09-02)

The platform has a "download everything" button, and its bundle turned out to be
simpler than the per-month downloads it replaces: a FLAT list of exactly the same
CSVs, same names, same header, same bytes — checked on 2020_01 for both products,
where the parsed frames come out `.equals()` identical. There is no folder inside
and no new format. A monthly zip is a bundle of one, and that is the whole change:
`iter_zip_frames` walks members instead of assuming there is one.

DA and IM now come from `EnergyPrices_12.1.D_r3.1.zip` and
`ImbalancePrices_17.1.G_r3.1.zip`. LOAD has no bundle and keeps its monthly zips.

**The per-month DA/IM zips are deliberately not read.** They are the July
snapshot, and keeping two live sources for one product is the pair that drifts
apart — but keeping them on DISK is the point: they are what the old `yearly` was
built from, so the diff between the old numbers and the refreshed ones is still
reproducible from the repository alone. The globs are what separates the two, and
the difference is one character: `EnergyPrices_12.1.D_*.zip` matches the bundle,
`*_EnergyPrices_12.1.D_*.zip` would also swallow every month. A test pins it.

**The window is one setting, not a glob.** `history.month_from` = `2020_01` is
where the methodology starts — the bundles themselves reach back to 2013/2014.
`history.month_to` is left EMPTY, meaning the last CLOSED month, computed in UTC
so it cannot go stale and cannot depend on which machine runs the build. History
is made of finished months: the bundles carry the month in progress (three days
of September when this was written), and a partial tail adds nothing to an annual
table while breaking the one thing dated snapshots are for — the next download
would carry a DIFFERENT partial month, and a diff meant to show backfills would
show that instead.

Filtering happens on the member NAME, before decompression: of the 143 members in
the DA bundle, 62 are never touched.

### The auction gate, the 09:40 run and the catch-up slot (2026-09-17)

**A decision issued after the auction has closed is not a decision.** The
day-ahead gate is 12:00 market-local on the day before delivery — 10:00 UTC in
summer for NL, 11:00 in winter — and `period.auction_gate()` computes it from
the market's own clock rather than storing either number, because the two are
one rule seen twice and RO is not on CET at all. `forecast()` checks it FIRST,
before the data: no amount of backfilling reopens an auction. The refusal
publishes as `<no_forecast reason="after_gate" />`, with no `missing_day` —
nothing is missing, the window simply shut.

This corrects advice that stood in this file for two weeks. "Backfill and re-run
TODAY" was wrong: the window to recover a forecast is not until midnight, it is
from the decision run to gate closure — half an hour, in summer. Several
forecasts recovered by hand in early September were issued after the gate. The
numbers were causal (data through D-2 only), but a bid nobody could submit earns
nothing, and the benchmark claims to measure what a rule would have EARNED.

**The decision run moved 09:30 -> 09:40**, so its four retries end around 09:56
instead of 09:50 and use the window up to the gate. Ten more minutes of
tolerance for a late source, and no less margin than before in any run that
behaves — but the margin is now thin enough that it is CHECKED rather than
assumed. `poll_times_utc` moved with it: left at 09:30 it would have silently
spawned a separate poll job ten minutes before the decision.

**A second slot at 14:00 UTC (`catchup`) that never forecasts.** Update, score,
publish, status, backup. It exists because twice in two weeks a day was lost for
want of a human at the keyboard, and because data that arrives at lunchtime
should still land in the store and still get scored. It is unconditional: the
store append is idempotent, so on a normal day it costs three log lines and one
request. It carries NO forecast, and that is the point — by 14:00 the auction is
four hours gone.

Note what this does and does not fix. Late data now lands by itself and settled
days get scored by themselves. A lost FORECAST is still lost: its only recovery
window is 09:40 to the gate, and nothing in this design extends it.

**The `<parameters>` twin is closed** — the one flagged on 2026-09-01 and left
open. `n_days_trailing_bias_default`, `final_day_of_month` and `run_time_utc` are
stamped into the row at computation time and rendered from there, exactly as the
version numbers are. Moving `run_time_utc` is what came for it: read at render
time, the new value would have rewritten what every past file claims and the
frozen-file check would have refused all 89. Existing rows were migrated to
09:30 / 20 / 3, and publication re-renders byte-identical: `0 written, 48
already identical, 0 refused` and `0 written, 41 already identical, 0 refused`.
`causality` stays a constant in `publish.py`: it is a statement about the
method, not a tunable.

### Schema 4 — the published vocabulary (2026-09-14)

The five values got public names, so that what the report calls a benchmark and
what the XML calls it are the same word. Internal columns keep their terse
working names; the mapping lives in ONE place, `PUBLISHED_NAME` in `publish.py`,
because renaming inside `benchmarks_core` would rename the columns of
`yearly_fixed.csv` — the frozen reference `validate_as_of` checks the whole
as-of path against — and breaking the proof to relabel the shop window is the
wrong trade.

| internal | published |
|---|---|
| `action_pnl` | `trailing_bias_value` |
| `ideal` | `extractable_value` |
| `devil` | `adverse_value` |
| `always_buy` | `passive_da_buy_value` |
| `always_sell` | `passive_da_sell_value` |

Also in schema 4: `n_days_default` -> `n_days_trailing_bias_default` (the window
belongs to the benchmark it parameterises), and a one-line `<action_codes>`
saying +1 is buy on the day-ahead auction and -1 is sell. `action` itself keeps
its name — the codes are explained once, in prose, and not spelled into every
attribute.

**One column per benchmark, and the family grows sideways.** A model arriving
later adds `neural_network_model_value` BESIDE these, with its own schema bump;
it does not take over an existing column. That is why `action_pnl` became
`trailing_bias_value` rather than something neutral: the column will always mean
what the trailing-bias rule earned. The consequence for that day is that
`score()` must compute each benchmark from ITS OWN action instead of deriving
one value from a single `action` field.

**The vocabulary is gated on the row's schema** (`_v4` in `publish.py`), and this
is not decoration. Renaming, the parameter key and `<action_codes>` are all
RENDER-time changes, and publish re-renders every historical group on every run:
applied unconditionally they would make all 86 files on disk differ from
themselves and be refused, exactly the storm the version stamp caused on
2026-09-01. A file speaks the language of its own schema. Verified after the
change: `0 written, 46 already identical, 0 refused` and `0 written, 40 already
identical, 0 refused`.

`<no_forecast>` gained an optional `leg="DA"`, carried as a third part of
`skip_reason`. Rows written before it have two parts and still render.

**The gate is a rule, not scaffolding.** It first looked like a workaround for
keeping draft files renderable, and it is not: the numbers will keep rising —
5 went to the actionless score file, 6 arrives with the first model, adding its
own value column — and the invariant behind it is permanent. *A published file is rendered in the
vocabulary of its own schema, and history is never re-rendered in a newer one.*
Retroactive relabelling is the thing this project refuses, and refuses whether
or not anyone happens to be reading the old files.

What IS temporary is the *range* of vocabularies carried. Everything under
`outputs/` today is a working draft — schemas 1 to 4 accumulated in a month of
learning about gaps, outages and reports, which is the right pace for a training
loop and not a debt. When the PROD branch is cut, those drafts go, the surviving
history sits on one schema, and the branches for the older vocabularies can be
deleted with them. The mechanism stays; only the back-catalogue it speaks to
shrinks.

### The version belongs to the ROW, not to the settings (2026-09-01)

Raising the two numbers by hand was supposed to be free. It was not, and the
reason is worth keeping: `publish` re-renders EVERY historical group on every
run and compares bytes, while `_root()` stamped `<version>` from `settings.json`
at RENDER time. So the first morning after the bump, all sixty already-published
files differed from their own re-render and the frozen-file check refused each
one — sixty ERROR lines and a non-zero exit, for numbers that had not moved a
digit. Only the label had.

The noise was the small half. The dangerous half is what `--force` would have
done at that moment: relabelled July's results with September's methodology —
precisely the claim these two numbers exist to make impossible.

Two rules had quietly collided. "A published file is frozen" and "every file
carries the current version" cannot both hold the moment a version is raised,
because the version is global and every file changes at once.

**Fix: `forecast()` and `score()` write `schema_version` and
`methodology_version` into the row as it is computed, and `publish` renders them
from the row.** A result carries the version it was computed under, forever. An
old file re-renders byte-identical, and a bump touches nothing but what comes
after it. Migration of the existing tables was one pass: every row before
2026-09-01 is 2/1, the single pass after it is 3/2 — checked against the
published files, which carried exactly sixty stamps of `2/1` and one of `3/2`.
Verified by running the publication afterwards: `0 written, 32 already
identical, 0 refused` and `0 written, 29 already identical, 0 refused`.

**KNOWN TWIN, deliberately not fixed** (owner's call, 2026-09-01): the
`<parameters>` block in the same header — `final_day_of_month`, `run_time_utc`,
`causality` — is still read from settings at render time. `n_days` is not
affected, it already lives in the row. So the day one of those three settings
changes, this morning repeats exactly: every historical file differs by its
header alone and is refused. The fix is the same move, three more columns. Worth
doing BEFORE changing any of them, not after.

### The forecast REFUSES an incomplete input day (2026-08-31)

The score side has always refused a half-published day. The forecast side did
not, and that asymmetry cost two published forecasts before anyone noticed.

What happened. On 2026-08-30 the A85 request failed once with 503, the retry
succeeded with HTTP 200 — and the answer simply did not contain 08-29. The poll
looked healthy (`http_ok` all true), so the retry loop stopped, and the forecast
for 08-31 was computed on a window ending 08-28. On 08-31 the platform was down
all morning; all four attempts burned, and the run went on to publish a forecast
for 09-01 on the same 08-28 data — three days stale.

Why nothing caught it. `signal_for` takes the last `n_days` observations per
hour-of-day from the END of what is available. A missing day therefore does not
SHORTEN the window, it SHIFTS it: `n_obs` stayed at 3, `full` stayed true, and
the `<NA>`-on-short-window guard could not fire. The forecast came out formed and
confident. The only trace was `data_through` repeating the previous run's value —
recorded honestly, read by nobody.

**So the check is on the FRESHNESS of the input, never on `n_obs`**, which is
blind to exactly this failure. In `workflow_compute.forecast()`, before anything
is computed: the market day that ended last night (`target − 2`) must be present
in the matrix WHOLE. The matrix is the inner join of DA and IM, so one count
answers both legs; the expected PTU count comes from `market_day_bounds`, never
from a constant, or a DST day would be refused twice a year.

Whole or unused — no partial days. A forecast on a fraction of the evidence is
not the method this project publishes, and the owner's own test is the honest
one: *I would not trade on a day where I have no data.* If it turns out that
gaps in operational data are common, the honest response is to change the
METHOD in the open and say so — "we forecast on the freshest complete day, which
may be older than yesterday" — not to let the code quietly do it. That is a
conversation to have with users, not a default to slide into.

**A refused day is refused for good.** `_target_grid` always aims at "tomorrow
relative to the run", so no later run can target it again: by the next run those
hours are already delivering, and issuing an action for them is precisely the
non-causality `as_of` exists to prevent. The day is permanently absent from the
benchmark — no forecast, therefore no score. The one way back is a manual
backfill and a re-run on the SAME day, while tomorrow is still the same tomorrow.

The refusal is RECORDED, not silent, in three places:

- `forecasts.parquet` — one row per PTU, `action` `<NA>`, new column
  `skip_reason` = `input_incomplete:YYYY-MM-DD`. In the forecasts table and not
  a table of its own, so a delivery day keeps ONE history in ONE place: if a
  backfill lets a real forecast follow the same day, the two passes number
  together (`calc_iteration` 1 refused, 2 issued). `score()` drops `<NA>`
  actions, so nothing downstream can mistake it for a decision.
- the published file — a frozen `forecast_*.xml` carrying `<no_forecast
  reason="input_incomplete" missing_day="…"/>` and NO `<points>`. This is the
  one exception to "nothing computed, nothing published", and it is deliberate:
  an unformed signal is the method saying "not enough history yet" and stays
  fileless, while a refusal is us saying "we ran, the data was not there". A
  reader who finds a hole in the series cannot tell those apart, and it is the
  second one they need.
- `outputs/status.xml` — `status="no_forecast" reason=… missing_day=…` on the
  forecast element, so a reader sees the processes ran and the data did not
  arrive, rather than guessing at `with_signal="0"`.

`skip_reason` is absent from every row written before 2026-08-31; the publication
layer reads a missing column as "ordinary pass", so history still renders.

**How it actually went (closed 2026-09-04).** The gate was built on the Monday
and tested by reality the same week: the ENTSO-E API answered `Scheduled
maintenance` from 08-30 to 09-03, four days. It refused three runs in a row —
delivery days 09-02, 09-03 and (before the fix) the days that had already been
issued stale — and published a `<no_forecast>` for each refusal. Not one
unfounded forecast went out. On 09-03 the API returned, the three-day poll window
picked up 09-01 and 09-02 by itself, and the gate opened with `data_through`
exactly one day behind the target, as it should be. 08-29 and 08-30 were backfilled
by hand on 09-03, and 08-31 — the one day whose imbalance prices the platform had
genuinely not published — on 09-04, a full sixteen days before the monthly
re-fetch would have caught it anyway.

**And the part worth resisting.** Both forecasts that went out stale before the
gate existed turned out PROFITABLE: 08-31 `action_pnl` +73.98 on a three-day-old
window, 09-01 +324.31 on a four-day-old one. Meanwhile the worst day of the whole
series, 08-30 at −1111.36 against a devil of −1632.12, ran on a perfectly NORMAL
two-day window. There is no correlation here between staleness and loss, and a
sample of two proves nothing either way. The gate is not an expected-return
device. It exists so that a published number means what the methodology says it
means — a signal formed on the three preceding days — and on 08-31 it did not,
with nothing in the file to tell a reader so.

**Deliberately NOT changed at the same time** (owner's call, 2026-08-31): the
retry loop stays at 4 × 300 s and keeps meaning "transport failed", because
retrying a source that answers 200 with no data is theatre; the single 09:30
poll slot stays single until there is real statistics on ENTSO-E outages; and the
maintenance-503 handling stays deferred. Also NOT cleaned up: the two forecasts
already issued on stale data (08-31 and 09-01). This is the training repo — that
kind of debris gets dropped once for good when a PROD branch is cut, and until
then it is evidence.

**Version bump this requires** (raised BY HAND, by the owner, in
`settings.json`): `schema` 2 → 3, because the forecast document gains a shape a
previous parser would not expect; `methodology` 1 → 2, because the same input can
now produce a different output — where there used to be an action, there is now
a documented refusal.

### Recovering a refused day — the manual backfill

The refusal writes the command into the log, ready to paste. Read
`logs/workflow.log`; a refused run says:

```
forecast NL @ …: NO FORECAST for delivery day 2026-09-16 — the signal needs
2026-09-12..2026-09-14 whole (3 days) and 2026-09-13 is not.
09-13: DA 0/96, IM 96/96. This delivery day cannot be recovered by a later
run. To recover it, backfill and re-run TODAY:
uv run python -m src.update --from 2026-09-13 --to 2026-09-13 &&
uv run python -m src.workflow_compute forecast
```

**The gate covers the WHOLE window, since 2026-09-15 — and learning that took a
second incident.** The first version checked one day, `target − 2`, because on
2026-08-30 it was the freshest day that was missing. On 2026-09-15 the hole was
in the MIDDLE: day-ahead for Sunday 09-13 was never published (Acknowledgement
999, "no matching data found"), while imbalance for the same day arrived
normally. The newest input day was whole, the gate opened, and `signal_for`
reached past the hole to 09-11 — three days of evidence spanning four calendar
days, with `n_obs` still reading 3. The same blindness as before; only the
hole had moved.

So all `n_days` days of the window must be whole. **One missing day refuses
`n_days` forecasts in a row**, because it sits in that many consecutive windows,
and that is the accepted price: the alternative is averaging across the gap,
which at this volatility is fitting rather than measuring. No interpolation, and
no "tolerate a gap of at most N" either — that N could not be defended.

`skip_reason` therefore lists every missing day of the window,
comma-separated, and `<no_forecast missing_day="…">` carries the list.

**The per-leg counts were added on 2026-09-14, and for a reason worth keeping.**
The line used to say only "0 of 96 PTU present on both legs" — true, and useless.
That morning the hole was in DAY-AHEAD: Sunday 2026-09-13 was simply never
published, while imbalance for the same day arrived on time. Every gap before it
had been in imbalance, so the owner read the line, assumed imbalance again, and
went through the previous day's log to find out otherwise. The CHECK is still on
the joined matrix and must be — a PTU is usable only when both sides of it exist
— but the joined matrix cannot say which side was missing, and that is the first
question anyone asks. Only the diagnosis gained the two counts; `_as_of_legs`
now keeps the legs apart so the refusal can name them.

That DA gap is also the first of its kind observed: DA for 09-12 and 09-14 were
both present, 09-13 was not, and two successive polls whose window covered it
returned two days out of three. A hole in the MIDDLE of the day-ahead series,
from a source that had published the days on either side.

Run it the SAME day, and only the same day — after midnight the target has moved
and the backfill can no longer produce that forecast, only the store rows. If the
source is still down, there is nothing to fetch and nothing to do; the day is
lost, and that is what the published `<no_forecast>` is for.

The ordinary poll window is three days, so an outage shorter than that heals
itself with no help. Past three days the window no longer reaches back, and the
missing days need `--from/--to` by hand once the platform returns.

### Scoring window — a delivery day is scored EXACTLY twice

`as-known` the first time the day is fully settled, `as-final` once after its
revision window shuts (`final_day_of_month` in settings, **20th of the following
month** — market practice is the 15th, and five days of margin cost nothing while
catching a still-moving value costs a wrong published number).

Why bounded at all: the naive "score everything settled, every day" grows
QUADRATICALLY — 96 rows on day one, 192 on day two, ~6 million after a year, and
all but a handful identical to the row before. Two passes make it linear, and
they are precisely the two versions the methodology asks for (`calc_iteration`
0 and 1), so no extra flag is needed: first and last row per `delivery_ts` IS
the pair.

A day is only scored when COMPLETE — every PTU present. Imbalance can arrive in
pieces, and half a day scored as though whole would sit frozen and wrong until
the final pass, with nothing in the data to reveal it.

The log now names each day and why: `delivery day 2026-08-06 (as-known), 96 PTU`,
or `not settled yet, 40 of 96 PTU published`, or `scored, next pass after
2026-09-20`.

### Scoring is driven by the STORE now, not by the forecast table (2026-09-18)

`score()` used to begin by dropping every forecast row whose action was `<NA>`.
A refused day therefore vanished before anything was computed — and with it went
four benchmarks that never needed an action in the first place.

`always_buy`, `always_sell`, `ideal` and `devil` are functions of the day's DA
and IM prices and of nothing else. They say what the MARKET did. Only
`action_pnl` asks what OUR rule earned, and only it needs a decision. Throwing
away four to protect one was never intended; it was what "iterate the forecasts"
quietly implied.

Found by the owner on 2026-09-18, reading the log: delivery days 09-15 and 09-17
were absent from the published series altogether, each because the day-ahead
hole of 09-13 sat somewhere in its signal window. The prices for both days had
been in the store the whole time.

So the candidate days now come from the store: every day it holds from
`scoring.score_from` onwards, PLUS every day an action was issued for. The
second half is not decoration — without it the days that predate the floor would
never come back for their as-final pass, and 36 of them were waiting for one.

**The floor exists because the store is seeded back to 2020.** Without it the
first run would write six years of history in a single pass, every row stamped
with today's `knownby_ts`. `scoring.score_from` is `2026-09-17`, the day the
defect was found, which is where the honest live series starts. **09-15 stays
absent** — it is before the floor and no action was issued for it. Widening the
floor is one line in `settings.json`, and the PROD cut is the moment to decide
how far back the published series should reach.

**A day scored late gets a late `knownby_ts`, and that is correct** (owner's
call). It records when WE knew the number, which is what the field has always
meant; a schedule that slips or a platform that goes down moves it anyway. It
reads as the run time only when everything ran normally, and that is the
information it is supposed to carry.

The published shape is in the schema 5 changelog entry above. In the table, a scored day
with no action carries `action` and `action_pnl` as `<NA>` and a `skip_reason`
copied from the refusal, so the day explains itself without a join to the
forecasts.

One defect fixed on the way: `action_pnl` was `np.where(action == 1,
always_buy, always_sell)`, which sent everything that was not `+1` down the
sell branch. Harmless only because rows without an action never reached it —
exactly the assumption this change removes. It is a three-way choice now.

### The zone became a parameter (iteration one, 2026-09-20)

Four commits, NL only throughout, done between the day's runs with the schedule
paused — never across a decision run, because a forecast missed is a forecast
lost. Acceptance was the same test each time: the tests pass AND `publish
--kind both` re-renders the whole archive to `0 written, 0 refused`. A refactor
that moves a published byte is not a refactor.

**1. Rename.** `workflow_nl.py` -> `workflow.py`, `update_nl.py` -> `update.py`,
`backup_nl.py` -> `backup.py`, `run_nl.sh` -> `run.sh`, logger `nl_workflow` ->
`tradinglab`, labels `com.tradinglab.nl.*` -> `com.tradinglab.*`, store
`data/processed/nl/nl_{da,im}.parquet` ->
`data/processed/zones/NL/{da,im}.parquet`. One folder per zone, named by the
AREA CODE — the identifier the logs, the raw filenames and the published paths
already use — and the files inside carry no zone in their names, because the
folder said it once and a name repeated is a name that can disagree with
itself. `make_launchd --install` now sweeps the legacy `*.nl.*` plists: a plist
left in LaunchAgents keeps firing with nothing to say so.

Renaming first was the point, and it paid immediately. Two rules turned out to
be about NL rather than about correctness: `update` refused any currency but
EUR (it now refuses only SEVERAL currencies in ONE document, which makes a
row's unit ambiguous in any zone), and `seed` demanded EUR on both legs (it
reports what it saw). RO settles imbalance in RON; neither was an error.

**2. One process, every zone.** No default area anywhere — a caller that forgot
to name a zone would otherwise keep working, silently, on whichever came first;
a test pins that the signatures have no default. The isolation contract lives
in ONE function, `for_each_area(fn, log, step)`: a zone that raises is logged
WITH its traceback (through the logger — an unhandled one goes to stdout, which
under launchd is a different file, and that cost a morning on 2026-08-09), the
loop continues, and the step reports "2 of 25 zones failed" with the exit code
carrying the count. Per zone now: store, poll log, the delivery-day window (the
market day is the zone's own) and a row in `status.xml`. A zone whose status
element cannot be built is written as `unavailable` rather than taking the file
down — a status file that fails to be written is the one failure it may not
have.

**3. Results in one table.** `data/processed/results/{forecasts,scores}.parquet`
across all zones, migrated with `workflow_compute migrate` (idempotent; the
per-zone files are left on disk, because a migration that deletes its own input
cannot be checked afterwards). Reasoning in `MAP.md`: the store is machinery
and splits by zone, the results are the product and do not.

**4. The auction gate was WRONG, and only RO would ever have shown it.**
`auction_gate()` took 12:00 in the ZONE's timezone. Right for NL by coincidence
— NL is CET — and an hour early for RO, where the gate is 12:00 CET = 13:00
EEST = 10:00 UTC. The 09:40 decision run would have sat past an imaginary gate
and refused every RO forecast as `after_gate`, source and data perfectly
healthy. Day-ahead is ONE coupled auction, so the gate is ONE instant and it
now lives in `settings -> day_ahead` (12:00 Europe/Brussels); `auction_gate()`
takes no area. **The gate moves in local time from zone to zone; the auction
does not move at all.**

Worth keeping: the old test asserted 09:00 UTC for RO. It pinned the BEHAVIOUR,
so it agreed with the defect and would have defended it. The replacement pins
the rule — one UTC instant for everyone, reading 12:00 in Amsterdam and 13:00
in Bucharest, summer and winter.

**Also fixed, and found by the first as-final pass the day before:** one
`knownby_ts` is not one delivery day. That pass graded twenty-six August days
in a single instant, and `status.xml` reported whichever row came first with
`ptu="2592"` — a number no delivery day can have. The element now describes the
pass: its newest day, that day's PTU, and `days_in_pass` when it covered more
than one.

### Exchange rates in the live path (iteration two, 2026-09-22)

NL never needed a rate — EUR is a unit — and that is exactly why nothing
refreshed `data/fx/` for two months. RO settles imbalance in RON, so the live
path now keeps the table current by itself.

**`src/fx.py`, a step in `run.sh` before anything is valued** (daily and
catchup). One request for `eurofxref-hist-90d.xml`, saved to `data/raw` with a
sidecar like any other source, copied to `data/fx/` as the working input, and
the daily table rebuilt. The 90-day file rather than the one-day file: the
one-day file carries a single publication, so one failed morning loses that
day's rate forever. A failure here is counted in the exit code and nothing
waits for it.

**The closed-day rule lives in the TABLE, not in the valuation.** Past the last
publication the table extends only over days on which the ECB was CLOSED —
weekends and the six TARGET closing days (1 January, Good Friday, Easter
Monday, 1 May, 25 and 26 December) — and stops at the first open day. The
calendar is computed (`parse_fx.ecb_closed`, Easter via dateutil), and was
checked against `eurofxref-hist.xml`: it reproduces every publication day since
2002 without one disagreement. The ECB office holidays that are NOT TARGET days
(Ascension, Whit Monday, 24 and 31 December and the rest) all carry rates, which
is why the list the owner found on the ECB site shrank to six days a year.

**A missing rate is a refusal, not a crash, and never a fill.**
`build_matrix(on_missing_fx=...)`: the report keeps "raise" — a frozen table is
never built on a partial valuation — and the live path uses "drop", which leaves
out what cannot be valued and names the dates. The existing gates then do the
rest. The forecast refuses; when both price legs are whole and the day is
still short, the refusal says `leg="FX"` and prints `src.fx` as the remedy
rather than an ENTSO-E backfill that would change nothing. The score simply
waits: scoring is driven by the store, so the day stays a candidate and is
graded by itself once the rate lands. A lost forecast is lost; an unvalued
score heals.

**"Not yet" is not "missing" (2026-09-24).** The rate for a date appears on the
afternoon OF that date — concertation 14:15 CET, published about 16:00 — which
is after both of our runs. A zone that publishes imbalance intraday puts
today's PTU in the store all morning, so today's rate is legitimately absent
every single morning. The first RO run said so in a WARNING, which would then
have appeared daily for ever; a warning that appears daily is one nobody reads
on the day it matters. `parse_fx.rate_due(d, now)` draws the line — a rate is
due if the day is not an ECB closing day and its publication hour has passed —
and only an overdue rate is worth a word. Nothing else changes: those PTU are
dropped either way, and they belong to a day that is not settled and cannot be
scored.

**Currency is read, and expected, and the two are compared.** Every poll row
now records the currency of its document. The zone registry carries
`expect_currency` per leg (RO: DA EUR, IM RON); a mismatch is a WARNING in the
log and a `currency_unexpected` attribute on that zone's `<source>` in
`status.xml` — present only when something is off, so an ordinary status file
keeps its ordinary shape. Never a stop: the day a zone joins the euro, the data
keeps flowing and the system reports what happened.

For NL all of this is invisible, and was checked that way: publish re-renders
to `0 written, 0 refused`, status unchanged.

### A zone joins in SHADOW (iteration three, 2026-09-23)

`settings.json -> zones -> <AREA> -> mode`, `"shadow"` or `"live"`, and there is
NO default: adding a zone means saying what it is for. Defaulting is wrong in
both directions — `live` would publish a zone nobody has watched, `shadow`
would quietly unpublish a live one if the field ever went missing. A zone in
the registry without a mode fails by name, and the per-zone isolation keeps
that to itself.

**Shadow runs everything and writes nothing.** Poll, store, forecast, score —
computed and logged, with `persist=False`, exactly as a hand-run with an
explicit `current_ts` already behaved. No row in `results/`, no file in
`outputs/`. The price store IS written, or there would be nothing to watch.
Promotion is one word; the first run after it writes.

What that buys is the answer to the questions this project refuses to guess:
when the TSO actually publishes imbalance, whether the input gate opens at
09:40, whether the rate is there. And any code still shaped like the first zone
fails in a log line instead of in a frozen published file.

`status.xml` carries `mode` on each `<area>`, so a reader who finds a zone with
no forecast and no score is told it is being watched rather than left to guess
it is broken.

**RO is seeded and in shadow since 2026-09-23.** From the history feathers:
DA 233 760 rows, IM 233 723, 2020-01-01 .. 2026-08-31 — then the gap to today
by polling. Two things the seed said out loud, neither of them in this document
before:

- **RO day-ahead was quoted in RON until 2021-06-17 and in EUR since.** One
  clean switch inside our own history, in the middle of a month. It is the case
  for reading the currency from the document rather than from a setting, made
  by the data: a currency is permanent until it is not, and no configuration of
  ours would have known. Both are stored as published and converted per row, so
  the years before and after are equally valid.
- **RO imbalance is RON throughout**, as expected.

The refusal's recovery command now names the zone
(`src.update --from … --to … RO`): with more than one zone, re-requesting every
zone to fix one is not a fix.

### The gate is per HOUR now (2026-09-26)

RO skipped one quarter-hour — 10:00 UTC on 2026-09-25, absent from three
successive polls that covered it, so not late but skipped. Under "the window
whole or nothing" that cost THREE forecasts, because the day sits in three
consecutive windows. One 96th of a day, three days of the benchmark.

**The rule now matches the granularity the method works on.** The signal is a
mean per hour-of-day over the last `n_days` observations of that hour. So an
hour needs its own four quarters in every day of the window, and it does not
care whether some other hour of the same day is short. An hour whose window is
whole gets an action; an hour with a hole anywhere in its window gets none.

`workflow_compute.incomplete_hours()` returns the short hours with the days and
counts behind them. Hours are UTC, which makes the arithmetic exact: a market
day holds each UTC hour-of-day once, so the expected count is four — except on
a daylight-saving day, where one hour occurs twice or not at all, and the
expected count therefore comes from the day's own grid (`hour_grid`), never
from the constant 4.

**The old rule is the special case, not a second rule.** A missing DAY is the
dangerous one: `signal_for` takes the last n_days observations from the END of
what exists, so an absent day does not shorten the window, it SHIFTS it, with
`n_obs` still reading n_days — that is the 2026-08-30 failure and the
2026-09-15 one. An absent day fails all twenty-four hours, nothing forms, and
the day is refused exactly as before. A missing quarter-hour shifts nothing.

The PARTIAL case is new and is schema 6: the file carries its `<points>` with
actions on the hours that formed, and one `<partial_input reason="..."
missing_day="..." leg="..." hours="10">` saying which hours were withdrawn and
why. A pre-6 row in that state is refused by the publication layer rather than
rendered quietly. Rows carry the reason per row (`hour_incomplete:<days>:<legs>`
— the hour needs no naming, the row IS the hour), so one parser reads both the
day-level and the hour-level refusal.

**Scoring changed with it, by the owner's call.** `scorable` used to mean
COMPLETE; it now means the market day has ENDED and left something behind. A
day that is permanently 95/96 would otherwise never be scored and would print
"not settled yet" for ever. It is scored on the PTU it has, and the file says
how many (`ptu="95"`) — the honest statement being "this is the sum over the
quarter-hours that exist". Two consequences, both accepted: an as-known pass
taken while a day was still filling can differ from its as-final pass, which is
information rather than a defect; and annual sums mix 95- and 96-PTU days,
which is what the monthly coverage rule already exists to handle. A day that
ended with NOTHING published is now reported as exactly that, and is the only
case that waits for ever — correctly, since there is nothing to grade.

**Version bump this requires** (BY HAND, by the owner): `schema` 5 → 6 for the
`<partial_input>` shape, and `methodology` 2 → 3 — the same input now produces
a different output, where a whole day used to be refused and 92 hours are now
decided.

### The publisher belongs to the row too — the third twin (2026-09-26)

Identity was deliberately kept OUT of the structure: element names are frozen
the moment anything is published, while a project name and a domain get
rebranded and move, so `<publisher name="..." url="..."/>` was the place where
content could change without a schema bump. That reasoning is right about the
FORMAT and wrong about the FILES. `publish` re-renders every historical group on
every run and compares bytes, so the day `PowerTradingLab` and
`powertradinglab.org` went into settings, all 135 published files would have
differed from their own re-render and the frozen-file check would have refused
every one. Exactly the storm of 2026-09-01, for the third time and the same
reason.

So `publisher_name` and `publisher_url` are stamped into the row at computation
time and rendered from there, like the two version numbers and the parameters.
**A file says who published it.** A rename then touches nothing but what comes
after it.

Order matters, and it is one command:

```bash
uv run python -m src.workflow_compute migrate   # stamps the CURRENT publisher
uv run python -m src.publish --kind both        # must be 0 written, 0 refused
#   ... only now rename publisher_name / publisher_url in settings.json ...
```

The migration stamps what settings say at the time it runs, which is what those
files were actually published by. Renaming first and migrating afterwards would
stamp the NEW name onto old rows and refuse the archive — loudly, and correctly.

Also fixed on the way: `_append` now reindexes instead of selecting columns. A
table written before a column existed is missing it, not broken, and the column
list grows over time — selecting raised a KeyError on exactly the old rows a
migration exists to bring forward.

### An incomplete hour carries no signal — the owner's ruling (2026-09-27)

Stated in one line, and it settles a class of future questions rather than one
case: **an hour that is not whole has no trading signal, full stop. There will be
no interpolation — it is outside the methodology.**

So the per-hour gate is not a defensive measure to be relaxed once the zones get
noisier. It is the method. RO skipped a quarter on 09-25 (10:00 UTC) and another on 09-26 (11:00 UTC).

**Corrected on 2026-09-28, and the correction matters more than the original
claim.** On 09-27 this file said neither gap was ever backfilled and called one
missing quarter a day RO's normal behaviour. The next morning the 09-26 gap was
gone — the source had filled it — while the 09-25 one had not moved. The
difference is not RO's: 09-26 was still inside OUR three-day poll window and
09-25 had fallen out of it. **A gap survives because of the window we chose, not
because the source refuses to repair it.** Three days of observation looked like
evidence and were not; the window was the confound.

This is already handled, by machinery that exists for exactly this: the monthly
re-fetch on the 20th goes back over the previous month, and the as-final pass
regrades. A day recorded as 95 of 96 as-known can legitimately become 96 as-final.
That is what scoring a day TWICE is for, and it is the first time the second pass
has had real work to do.

What stands unchanged is the rule and its price. An hour that is not whole gets
no signal, so a zone with occasional holes publishes fewer than 96 signals: 92 on
2026-09-28, 88 the day before. The number moves with the window's contents and is
not a constant.

The alternative — filling the hole from the neighbouring quarters — would put a
number we invented inside a benchmark whose whole claim is that it never invents
(rule 9). A thinner signal is a smaller product; a fabricated one is not a
product at all.

### The log reports a PASS, not a day (2026-09-27)

Scoring printed one line per delivery day. That was right while a run scored one
day, and wrong in the two situations that score many at once:

- **A zone in shadow.** Nothing is stored, so `first_done` is empty and every day
  since the floor is scored again every morning: 18 lines on 2026-09-25, 10 on
  09-26, and one more every day for as long as the zone stays in the dark.
- **The as-final pass on the 20th.** A whole month in one go — the same shape,
  arriving in every zone that goes live, so this was never only a shadow problem.

`_log_scored` now reports, per reason, the NEWEST day in full and the rest in one
summary line: how many, over what span, how many carried an action, and how many
were short of a full day. That last count is the only per-day fact worth keeping
— a source skipping PTUs is news — and it survives as a number. Everything else
is in the results table, which is where numbers belong. Two reasons can occur in
one pass (yesterday as-known plus last month as-final), so the report is at most
four lines whatever the zone count or the month length.

Two smaller things in `_log_waiting`, same principle:

- **A day that has not begun is not a day with nothing in it.** Tomorrow's
  day-ahead prices put tomorrow in the store, so it becomes a scoring candidate
  before it exists, and "still being delivered, 0 of 96 PTU published" was true
  and useless. Those days are now counted on one line. A day genuinely in flight
  keeps its own line — that one is a real question.
- **A day that ended empty is said once per run.** NL 2026-09-13 lost its
  day-ahead and will never be gradable; it had been announcing itself every
  morning for two weeks.

No output file moves: this is the journal only. 87 tests, two of them new and
both about line COUNT rather than line text, because the defect was volume.

### The site gets its data (2026-10-01)

Three decisions and one module, all live the same morning.

**Drafts are cut in the service, not on the site.** The site session first
proposed to hide the days before 09-17 on the pages. The owner's call was to
cut them in `summary.py` instead: v1 is the public contract, and a cut made on
the pages would still leave the drafts in the CSV files offered for download.
The date is `publication.public_from` (2026-09-17), a key of its own and not
`scoring.score_from`. They hold the same date today and mean different things:
the scoring floor decides what the store puts forward for grading — and days
before it are still graded when an action was issued for them, 36 NL days wait
for their as-final pass on that rule — while the public floor decides what a
reader is shown. The PROD cut may move one and not the other. Whole days are
dropped, so the pass ordinal of a surviving day does not change.

**The archive is cut with it.** The server pushes to `powertradinglab-site`
only `v1/`, `status.xml` and the archive files a v1 row cites. A draft XML is
on disk and in the private backup, and never in a public repository. The cut
is made once, in `summary`; `site_push` follows it.

**`src/site_push.py`** — last step of `run.sh`, after the backup. Its own
checkout `~/ptl-site`, its own write deploy key `~/.ssh/ptl_site`, settings in
the `site` block. It owns ONE folder of the site repository, `data/`, deletes
it and rebuilds it on every run — a mirror, not an append, unlike the backup,
because a file that leaves the published set must leave the site too. The
folder name is checked before anything is deleted: an empty or climbing name
would turn "rebuild data/" into "delete the repository". Two writers share the
repository, so every run starts from the remote's newest state, and a rejected
push is retried once. A run that changes nothing commits nothing. Why the
server does not read through the backup repository instead: the backup holds
`data/raw`, and a key to it in the CI of a public repository is the leak the
separation exists to prevent.

**Forecasts in v1**, by analogy with the scores and on the same floor:
`<ZONE>_forecasts.csv`, `-90d`, `-latest`, and `forecasts-latest.csv`. The
decision is counted in PTU — `ptu_buy`, `ptu_sell`, `ptu_no_action`, which sum
to `ptu` — and the per-PTU action stays in the XML (owner's call: no hourly
profile). `skip_reason` separates REFUSED from merely unformed, as in the
table. A day with no signal on any PTU and nothing refused gets no row: publish
writes no file for it, and a row could not name its source. The newest forecast
row is published at ~09:40 UTC, before the gate — a dated public commit made
before the prices exist, which no score file can show.

Measured on the first pushes: 36 files with scores alone (`1f05117`), 61 with
forecasts (`a9d9772`): 9 + 7 v1 files, `status.xml`, 26 score and 18 forecast
XML. A second run said `nothing changed`. Real cases for the site's three
states are already in the data: NL 09-17 refused (`input_incomplete:2026-09-13:DA`),
RO 09-17..27 with no forecast at all.

**Versions differ between rows of one v1 file** — NL 4–5 / 2, RO 6 / 3 — which
is the version-belongs-to-the-row rule seen from the reader's side.

### What is NOT done — the list as it stands on 2026-09-29

Written at the end of the cowork session that put the service on a server, so
the next one starts from facts instead of archaeology. Grouped by what kind of
thing each is, because "open item" covers three different urgencies.

#### Holes — something we believe is protected and is not

1. ~~**`data/fx` is not in the backup.**~~ **Closed the same day.** Found while writing this list, and fixed by the owner within the hour.
   `data/fx/eurofxref-hist.xml` is the whole ECB rate history since 1999, 7.9 MB,
   fetched once by hand; `nbu_fx_uah.xml` likewise. Neither is in `data/raw`,
   because the server only ever fetches the 90-day file. So the private backup
   holds everything EXCEPT the rates before the last ninety days. Losing the disk
   would leave nothing to value RON before 2021-06-17 — the Romanian history in
   the store, and the 2020-2026 report's inputs. Both files are re-downloadable,
   but so was the archive, and we back that up. The fix was one line —
   `data/fx` added to `backup.paths` — costing 8.7 MB once and 70 KB a day
   afterwards. Kept here as an entry rather than deleted: the hole existed
   because "back up the cause, not the effect" was applied to ENTSO-E and not
   checked against the second source, and that is the mistake worth remembering
   when a third source arrives.

2. **Nothing rebuilds the store from `data/raw`.** The backup deliberately leaves
   the store out, on the argument that it is a fold over raw and raw keeps every
   response with its fetch time. That argument is sound and the code does not
   exist: the 2020-2026 seed came from the bulk archive, not from raw. Until it
   is written, the store's protection is the provider's disk snapshots alone. The
   rebuilder is also worth having for its own sake — running it and diffing is
   the only check that the store agrees with its inputs.

3. ~~**The server cannot publish to the site.**~~ **Closed 2026-10-01** — see
   "The site gets its data". Kept as written: There is no deploy key on
   `powertradinglab-site` and no push step in `run.sh`. The site will have
   nothing to build from until both exist. Same shape as the backup push: a key
   scoped to one repository, last step of the run, failure counted in the exit
   code and fatal to nothing.

#### Waiting on time — nothing to do but watch

4. **RO is under observation, and no conclusions yet** (owner's instruction,
   2026-09-28: "рано выводы делать"). Two things are accumulating. The
   publication lag: 12 PTU at 09:40 UTC and about 67 by 14:00, on both 09-28 and
   09-29, which looks like a morning batch rather than a steady half-hour lag but
   is two observations. And the skipped quarter-hours: 09-25 and 09-26 each lost
   one, 09-26's was refilled by the source, 09-25's was not — see the correction
   above about the poll window being the confound. After a few more days, one
   proper entry, once.

5. **2026-10-20 is the first real as-final pass.** Twenty-one NL days and eleven
   RO days are queued for it, and the monthly re-fetch runs first. It is the first
   time the "a day is scored exactly twice" rule does work rather than ceremony,
   the first chance for a short day to become whole, and the first time `publish`
   writes a second file for a day that already has one. Watch it deliberately.

6. **The Hetzner backup price is unverified.** 20 % of the server price is what
   the console showed at purchase, not a figure from a price list. The October
   invoice settles it; the table in `HOSTING.md` says so.

#### Next to build

7. ~~**Forecasts in v1.**~~ **Closed 2026-10-01** — see "The site gets its
   data". Kept as written: The same three files as the scores, by analogy
   (`<ZONE>_forecasts.csv`, `-90d`, `-latest`). Deliberately left out of the first
   version — adding to a public contract is cheap and removing from one is not.
   Until they exist, no page can say "we declined that day".

8. **The site**, in the neighbouring cowork, from `docs/SITE.md` as rewritten on
   2026-09-29: the generator lives in the site repository, the build runs in
   Actions, the site reads `outputs/v1` and parses no frozen XML.

9. **DNS.** `powertradinglab.org` onto Pages, `.com` redirecting to `.org`.

10. **The PyPI package** `powertradinglab-benchmarks` (import `powertradinglab`),
    in its own repository, after the v1 files have stood unchanged for a week.
    A client for a contract that is still moving is a promise we would have to
    break.

11. **ENTSO-E maintenance 503s still burn four retries** and log four errors per
    outage day. Deliberately unwritten until there is enough history to say how
    the platform behaves — see "The early plan, and the four things that survive
    it".

#### Housekeeping, none of it urgent

12. **Clean the `*.md` before opening the repository.** One real decision inside
    it: whether `HOSTING.md` keeps the server's IP address and user name. They
    are not secrets — the machine is key-only with one port open — but they are
    an invitation to noise.

13. **The 14:00 catch-up slot.** It was to be switched off once 09:40 proved
    reliable. It has since earned its keep twice over: it is what picks up RO's
    afternoon catch-up, and it is a second backup commit each day. Revisit
    deliberately rather than by drift.

14. **The Mac's launchd jobs** are unloaded and kept as the way back. Remove them
    when the way back stops being needed.

15. **Legacy per-zone `forecasts.parquet` / `scores.parquet` on the server**,
    left from before the results moved into one table each. Harmless, unread,
    and worth deleting so nobody later mistakes them for data.

### The v1 data interface — the reader's shape (2026-09-28)

The frozen XML is the RECORD: one file per zone per delivery day per pass, never
rewritten, every PTU, every parameter. That is the right shape for an archive and
the wrong shape for anyone who wants "the last ninety days of RO". `src/summary.py`
builds the reader's shape beside it, after publication, on every run.

```
outputs/v1/index.json            what exists, the vocabulary, checksums
outputs/v1/zones.json            one passport per zone
outputs/v1/scores-latest.csv     one row per zone — the front page
outputs/v1/NL_scores.csv         all of it
outputs/v1/NL_scores-90d.csv     the last 90 delivery days
outputs/v1/NL_scores-latest.csv  the newest finished day
```

**Flat, not nested, and the underscore is load-bearing.** Twenty-five zones give
seventy-odd files in one directory, which is nothing for a machine and what
`index.json` is a map for; the archive is nested because it grows without bound,
the summary is not. The separator is `_` and appears exactly once, because zone
codes carry hyphens of their own — `DE-LU`, `IT-North` — and a hyphen would leave
the boundary unparseable. No prefix means every zone. (The flat layout is the
owner's call, against a first draft with per-zone folders; the hyphen argument is
what settled it.)

**One row per zone per delivery day, newest pass only**, with `pass` and
`calc_iteration` saying which pass that is — the store's own rule, keep the
versions and collapse at read time, applied to the shop window.

**`ptu` and `ptu_with_action` are columns, not footnotes.** The values are sums
over the day, so a day the source left short is mechanically smaller for a reason
that has nothing to do with the market, and a trailing bias computed on 92 of 96
PTU is not comparable with one computed on 96 unless the denominator travels with
it.

**`source_file` in every row.** The traceability promise, kept mechanically: any
number on the site or in anyone's notebook names the frozen document that
established it. It is written only if that file is actually on disk, which is why
this step runs AFTER publish and never before — a citation must point at something
that exists.

**No wall clock anywhere.** `index.json` carries `generated_from` — the newest
`knownby_ts` in the data — not the time the run happened. The directory is
therefore a pure function of its inputs: identical results give identical bytes, a
run that changes nothing writes nothing, and the daily backup commit stops
recording that time passed. Rule 6 applied to a layer that is not itself frozen.

**Derived values only, per day.** Never a day-ahead or imbalance price. Per-PTU
benchmark values are close enough to the spread itself that publishing them in a
summary would be arguing with the licence rather than obeying it; per-PTU detail
stays in the archive, where it belongs.

Forecasts get the same three files later, by analogy, once this has run for a
while — the owner's call, and the right one: adding to a public contract is cheap
and removing from one is not.

**The test worth having:** per PTU the oracles are the max and the min of the two
passive positions, so over any day `extractable_value + adverse_value` equals
`passive_da_buy_value + passive_da_sell_value` exactly. Cross two public names on
the way out and that breaks at once. It held to the cent on the first real output
(NL 2026-09-25: 391.4750 + -1239.6125 == -814.3225 + -33.8150).

**A test that had to be fixed, not the code.** `writes_results("RO") is False`
failed the moment RO went live. It was pinning the roster instead of the rule, the
same mistake as the old auction-gate test, and it now asserts that a zone writes
exactly when its mode says live.

### RO went live (2026-09-28)

The flip is one line in settings — `zones.RO.mode: shadow -> live` — and the
first live pass did what variant (a) says it should: eleven delivery days,
2026-09-17 through 09-27, written and published at once as market values with
`<NA>` where no forecast existed, plus the first RO forecast, for delivery day
09-29. With NL's own new day that is `publish forecast: 2 written` and
`publish score: 12 written`, both with **0 refused** — the archive re-rendered
identically while twelve new files were added to it.

The numbers RO enters the record with: 09-27 graded at `ideal=2784.40`,
`devil=-2784.40` (single-price since 2026-07-01, so they mirror), against NL's
09-27 at `ideal=533.38`, `devil=-1136.32`. The factor of three to five holds.

Two things to watch rather than conclude:

- **The publication lag moved.** RO showed 12 of 96 PTU at 09:40 UTC, where the
  day before it showed 48 at the same clock position — about nine hours behind
  instead of half an hour. Grading is unaffected (only finished days are graded),
  but whether this is one late morning or a change in the source is worth one
  more observation.
- **The log will shrink again tomorrow.** Today `first_done` was empty for RO, so
  the pass reported one full day plus a summary of ten. From the next run it is
  one day.

### The backup is a private git repository now (2026-09-27)

The old step copied the store into dated folders in a Google Drive directory. It
had been warning every morning since the migration, and correctly: the folder is
on a laptop and the service runs on a server that never had it.

**What replaces it:** a snapshot pushed at the end of every scheduled run to `powertradinglab-backup`, a
repository that is private for ever and separate from the code. Separate is
structural, not tidiness — `data/raw` carries ENTSO-E market data we are not
licensed to redistribute, the code repository is about to be public, and a
visibility switch must not be able to publish data by accident. The server holds
a write deploy key scoped to the backup repository and to nothing else. No
licence file goes in it: a licence grants rights to whoever receives the code,
nobody receives it, and a licence sitting beside data we cannot relicense would
be a claim we are not entitled to make. A README carrying the private-only
warning is written by the code on first run, so it exists even if nobody
remembers to add it.

Live since 2026-09-27: the first snapshot is `0910784`, 827 files, 10.7 MB, and it
carries the August provenance that had been on the laptop only. The restore
procedure is written down in `docs/HOSTING.md` — a backup without one is a hope.

**What goes in, measured rather than guessed** (Mac, 2026-09-27):

| path | size | rewritten whole? |
|---|---|---|
| `data/raw` | 8.7 M | no — appended |
| `data/processed/results` | 320 K | yes, daily |
| `outputs` | 1.8 M, 139 files | no — frozen |
| `data/processed/zones` (store) | 24 M, ≈5 M per zone | **yes, daily** |
| `data/processed/fx_daily.feather` | 5.9 M | **yes, daily** |
| `data/processed/history_*.feather` | 724 M | dev cache, not a source |
| `data/archive` | 408 M | static, re-downloadable |

The rule that follows from the table: **git is good at what is appended and bad at
what is rewritten whole.** A parquet rewrite costs its full size in every commit —
5 MB per zone per day, 3.6 GB a year at two zones, 130 MB a day at twenty-five.
So the store stays out, and that is a claim, not an omission: the store is a fold
over `data/raw` by (delivery_ts, knownby_ts), and raw keeps every response with
the instant it was fetched. Whatever the store knows about when a value appeared,
raw knew first. Back up the cause, not the effect.

The results are the exception that proves the rule — they are not derivable from
raw at all, because they are what we DECIDED, and below the scoring floor nothing
will ever recompute them. 320 K a day is the cheapest insurance in the project.

**The hole, stated rather than papered over:** no code rebuilds the store from raw
today; the 2020-2026 seed came from the bulk archive. So the store is recoverable
in principle and not yet in practice. Two mitigations, and they do not compete —
a rebuilder (which is also a check that the store agrees with its inputs), and
the provider's own whole-disk snapshots at about €1.20/mo, which is the tool for
protecting something that git should not hold.

**Also found on the way:** the server's `data/raw` starts in September 2026, while
the Mac holds August too. The provenance record of the pre-migration era is on
the laptop only, and it has to be moved before the backup can claim to hold the
history.

If the backup fails it is logged and reported in the exit code, and nothing else
in the run waits for it. `mode: "dir"` still does the old dated-folder copy and is
the way back. The deploy key is the server's; a machine without it falls back to
its own git identity, which is what lets the Mac run the same step by hand.

### Logging

`setup_logging()` puts its handlers on the ROOT logger, so any module can just
do `logging.getLogger(__name__)` and land in the same file. That is what lets
the generic `ingest` layer log without importing anything from the NL workflow —
a library layer should not decide where logs go. (While ingest used `print`, its
lines arrived out of order against the logged ones, different buffers.)

A run started BY HAND logs `manual` and never claims to be late. Only
`run.sh` sets `TRADINGLAB_SCHEDULED`, so only a scheduled run is measured
against a slot — otherwise every manual command produced a false "machine
asleep" warning, and an alarm that cries wolf is worse than no alarm.

Every scheduled line carries the SLOT the run was scheduled for:
`2026-08-06T05:30:11Z slot 05:30Z INFO src.ingest: saved raw …`. launchd does not
tell a job which slot fired it, so it is inferred as the latest configured time
at or before now; if the gap exceeds five minutes the run says so outright
(`started 53 min after its 07:30Z slot`). Without this, a punctual run and a
catch-up after the Mac wakes look identical, and the only way to tell them apart
is reading file mtimes — which is exactly what we had to do on 2026-08-06.

`workflow.log` rotates at UTC midnight — UTC and not local, or the file boundary
would move when the owner changes country — keeping 90 files. Note the reason is
readability, not space: the workflow writes ~4 KB a day, about 1.5 MB a year, so
one endless file would have been fine to store and horrible to read.

`logs/launchd_*.log` is written by launchd itself (StandardOutPath), out of
Python's reach, and receives a copy of everything the console handler prints.
`run.sh` keeps it bounded: past 2 MB it moves aside to `.old`, one generation.

**Log volume follows how surprising the event is.** Two consequences, both from
reading the real log after a month:

- Days already scored and queued for their final pass are summarised into ONE
  line naming the earliest due date. A line each grew the log by one line per day
  per day, and said nothing new.
- A REVISION is spelled out, `was -> is`, up to ten PTU and then a count. It is
  rare and it is the one thing you would otherwise open the parquet to see. On an
  ordinary day, when nothing moved, this prints nothing at all.

### The store is VERSIONED now (parquet, key = delivery_ts + knownby_ts)

`data/processed/zones/<AREA>/{da,im}.parquet`. `write_store` no longer collapses to the
latest version per PTU — collapsing is `as_of`'s job, at READ time, because the
whole point is to be able to ask what was known at a past instant. One-off
migration from the old feather store: `uv run python src/workflow.py migrate`
(format change only, values untouched; the feathers are left on disk).

### update — polling as the measuring instrument

`uv run python -m src.update [--days N | --from D --to D]`. Chain:
`ingest.fetch_raw -> parse_da/parse_im -> diff -> store + poll log`.

- Each run re-requests a WINDOW of the last `window_days` delivery days (setting),
  not just yesterday. Late arrivals and revisions are then caught by the ordinary
  daily run, and filling a gap is the same command with a longer range instead of
  a one-off backfill script that would never be exercised again.
- **Only CHANGES are stored**: a row is written when the PTU is unseen, or when
  its value differs from the LATEST stored version. So `knownby_ts` reads as "the
  first time we saw this value", and as-known / as-final are simply the first and
  last row for a `delivery_ts` — no `calc_iteration` flag to maintain and nothing
  that can drift out of agreement with the data. A value reverting to an older
  one counts as a change (compared against the latest version, not against every
  version ever seen).
- **`knownby_ts` = the instant of the REQUEST**, read from the raw sidecar — NOT
  `<createdDateTime>`, which ENTSO-E regenerates per request and which therefore
  is our fetch time wearing a misleading name. `<createdDateTime>` is kept in the
  poll log, where it cannot be mistaken for a property of the data.
- **Poll log** `data/processed/zones/<AREA>/polls.parquet`, one row per request
  (fetched_ts, doc, period, http_ok, n_rows, n_new, n_changed, created_datetime,
  raw_file). Without it, "no new rows" is ambiguous between "nothing changed" and
  "we never looked". This table is the instrument for the publication-delay
  question: the gap between a delivery day and the first poll that returned its
  imbalance, to a resolution of the poll spacing. Hence `poll_times_utc` in
  settings has FIVE times across the morning, not one.
- Known A44 glitch handled: on HTTP 400 the request is retried once with
  `businessType=A62` (see the API section above).
- Currency: DONE, the live parsers now read `<currency_Unit.name>` (present in
  both A44 and A85, inside each TimeSeries) and emit a `currency` column, so the
  live path matches the File Library path. Several currencies in one document
  are REFUSED rather than resolved — that would make each row's unit ambiguous.
  `update` no longer assumes EUR: it CHECKS, and stops on anything else. The
  NL DA store gained the column too (`migrate` backfills EUR, which is correct
  rather than a guess: NL DA clears in EUR through SDAC).

### First measurement of the IM publication delay (2026-08-05)

The gap-fill run answered, provisionally, the question the validation left open.
At **08:35 UTC on 5 Aug** the A85 window returned:
- 4 Aug (the completed market day, which ended 22:00 UTC) — **all 96 PTU**;
- 5 Aug (the day in progress, ~10.5 h of it already delivered) — **nothing**.

So: yesterday's imbalance is complete on the platform ~10.5 h after the market
day ends, i.e. BEFORE the 09:30 UTC decision. That puts us on the good side of
the sweep threshold, and `shift(2)` in the report matches reality. Two caveats:
it is a single observation, and it is an upper bound — we know the data was
there by 08:35, not when it appeared. The five daily polls narrow that.

Second fact from the same run: NL imbalance is NOT published intraday through
A85. It arrives as a batch for the completed day, so there is no point polling
for the current day's PTUs.

Note the gap-fill itself found nothing to reconcile: the archive ended 2026-07-28
and the fetch started 07-29, so there was no overlap and the "value changed"
branch has not yet run on live data — it will on the second poll of any day.

### One zone registry (settings.json -> zones)

Area code, EIC and market timezone travel together, so they live together:

```json
"zones": { "NL": {"eic": "10YNL----------L", "tz": "Europe/Amsterdam"}, ... }
```

They used to be in three places — the EIC as a constant in `workflow` AND in
`workflow_compute`, the timezone in `period.ZONE_TZ` keyed BY the EIC. Adding a
zone meant remembering all three, and the two could disagree without anything
noticing.

**The AREA CODE is the project's identifier; the EIC is an API detail.** It now
appears only where a request is built. Everything else — logs, raw filenames,
sidecars, `period` — speaks in area codes, so a raw file is
`A85_ME_202607150000_...` instead of `A85_10YCS-CG-TSO---S_...`, which no one can
read at a glance. Old files keep the old names; nothing scans that tree.

A zone missing from the registry fails by name and lists the known ones, rather
than raising a KeyError on a code nobody recognises.

### THREE time entities was one too many — there are TWO (decided)

`delivery_ts` (the PTU being traded) and `knownby_ts` (when the row became known)
are the only time entities in the project, INCLUDING in our own computed tables.
A separate `run_ts` was proposed for the results and rejected: in live it is the
same instant as `current_ts`, and `current_ts` is not a third kind of time but
the as-of cursor. The wall-clock of a code run belongs in the log, not the data.

So a computed row carries `knownby_ts = current_ts` — the moment WE knew it. Our
outputs then have the same shape as our inputs, and `as_of()` reads them the same
way; that is how `score()` can only ever grade an action already issued.

Table key is `(knownby_ts, delivery_ts)`. Re-running the same `current_ts`
OVERWRITES its own rows instead of appending: the computation is deterministic,
so a second run must reproduce the first, and a difference is a bug rather than a
new version. With `run_ts` in the key that bug would have been filed silently as
an extra record.

### as_of vs shift(2) — pick ONE, never both

They are two ways to say the same thing, not two safeguards to stack:
  - `as_of(df, current_ts)` — the canonical rule. Keeps what was published by
    `current_ts`, so the lag emerges from reality. Live path, then
    `forecast_actions(..., lag_days=0)` / `signal_for`.
  - `lag_days=2` — the report's shortcut hardcoding the same 48 h, with no
    knownby_ts filtering at all.
Filtering AND shifting lags the signal twice (~5 days instead of 2).

### VALIDATED: the shortcut and the rule agree exactly (NL 2025)

`uv run python -m modelling.validate_as_of --sweep` replays 2025 day by day,
standing at 09:30 UTC before each delivery day with only the data known by then,
and compares against the report path and against `yearly_fixed.csv`:

- report path reproduces `yearly_fixed.csv` for NL 2025 to 0.0000 on all five
  benchmarks (so the NL store slice is faithful to the history feathers);
- hourly actions: **35 040 of 35 040 PTU identical**, yearly `stat_action_pnl`
  difference **0.00 EUR/MW**. Backtest == live is now measured, not asserted.
- gap target-day .. freshest fact: median 2.00 days, min 1.00, max 3.00. The
  spread is the DST days — a 23/25-hour day makes an hour-of-day occur twice or
  not at all. Both paths wobble identically because both count OBSERVATIONS of
  the same hour-of-day, not calendar days.
- Speed: each iteration slices the store to the last 20 days, since `signal_for`
  never looks past the last `n_days` per hour-of-day. Seconds, not hours. The
  run asserts `n_obs == n_days` on every hour, which is what proves the slice
  was long enough.

Archive `knownby_ts` is NOT usable for this: File Library zips are rewritten
after the fact (a Jan-2026 file can revise June 2025), so the stamp is a revision
time, not first publication. The validation therefore reconstructs plausible
publication instants (`--mode rule`: DA ~12:45 local on D-1, IM at a configurable
hour on D+1); `--mode raw` will only mean something once the stamps are fixed.

### The one open question this leaves: when does IM actually appear?

The sweep over the assumed IM publication hour has a hard threshold exactly at
the run time — IM for day X must be on the platform by 09:30 UTC on X+1 (11:30
local summer / 10:30 local winter):

      IM published    agreement   stat_action_pnl   vs report
      D+1 00:00 local   100.00%          -65,548            0
      D+1 06:00 local   100.00%          -65,548            0
      D+1 12:00 local    78.70%          -76,664      -11,116
      D+1 18:00 local    78.70%          -76,664      -11,116

Read this correctly: `n_days = 3` throughout. What moves is the RIGHT EDGE of the
window, not its length — either the decision sees yesterday's imbalance or it
does not, and in the latter case all three observations are a day older. It is a
difference between two DECISIONS, both valued on the same prices; it says nothing
about price revision (see calc_iteration above), which is a separate axis.

On NL 2025 the staler window did worse, but that is one zone and one year — not
yet grounds for "delay degrades the signal" as a general claim.

Which side of the threshold reality sits on cannot be answered from the archive.
It is `update` that will answer it, by recording what was visible at each poll
— which means **polling several times per morning, not once a day**: a daily poll
can only ever resolve the delay to the nearest day.
