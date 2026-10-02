# The site — brief

Written 2026-09-27 for a session that will build it, revised the same day after
the owner's review. Read `HANDOFF.md` for the project and its nine rules,
`HOSTING.md` for the machine. This file is what the site adds, what it must not
do, and how it is judged done.

## What the site is for

Two jobs, and they are not the same job.

**The service.** One question from a stranger: *was this market worth trading,
and is it still?* The site answers with numbers that were computed before the
fact and frozen, and it lets the reader check every one against the file it came
from.

**The owner's presence on the web.** A findable, stable page that says who built
this and how to reach her. This is a stated purpose, not a footnote: it decides
that `/chuchueva` must be indexable, must keep its address for years, and is
allowed to be the second-most-linked page on the site.

## The naming principle, and why the site must stay thin

From the owner, 2026-09-27, out of the project that came before: **mbureau.ru/energy
died of too much site.** A service that outlived several generations of its own
internals was finally killed by the weight of what had been built around it.

So: **PowerTradingLab is the platform, benchmarks are the first product.** In two
or three years something may be added or dropped, and that must not require
renaming anything. Concretely, for whoever builds this:

- The product appears in the PATH, not in the domain and not in the layout:
  benchmark pages and benchmark data live under `/benchmarks/…`. A second
  product later gets its own path beside it and touches nothing.
- The site is REPLACEABLE. It reads published files and holds no state of its
  own, so it can be rewritten from scratch, in another tool, without migrating
  anything. Nothing downstream may depend on the site's internals.
- "Lab" is meant literally: experiments, some of which end. Build for the one
  that ends.

## Hard constraints, inherited and not negotiable

- **Static files only.** No backend, no database, nothing rendered at request
  time. (The project's own lesson: 84% of the previous effort went to
  infrastructure and 16% to the alpha.)
- **The site is NEVER a dependency of the daily run.** The machine that decides
  before the auction gate does not serve the site and does not wait for it.
- **The site reads published files; it never recomputes.** Every number shown
  must exist in a file, and the page must link to that file.
- **No raw day-ahead prices, anywhere, including the summary files.** Imbalance
  prices are ENTSO-E under CC-BY 4.0; day-ahead prices belong to the exchanges
  and only DERIVED values may be published. A licence, not a preference.
- **There is no query API, and the site must not imply one.** Files over HTTPS,
  and the documentation says so in its first line.
- **The palette is the project palette** (`HANDOFF.md`): teal `#157A7F`, ink
  `#0E2A33`, amber `#E39B2F` sparingly, grey `#6B7780`, hairline `#D8DEE0`.
- **It works without JavaScript.** JS may add convenience and may never be
  required to read a value.
- **No tracking, no ads, no cookie banner, no login, no newsletter capture.**
  Visitor statistics are aggregate and server-side only: Cloudflare's own
  traffic analytics on the proxied domain (requests, approximate unique
  visitors, countries, paths). No cookies, no script on the page, no
  per-person data. Decided 2026-10-01.

## The data contract

Frozen artefacts, the source of truth, published by the workflow:

```
outputs/<zone>/YYYY/MM/forecast_<AREA>_<delivery day>_<knownby>.xml
outputs/<zone>/YYYY/MM/score_<AREA>_<delivery day>_<knownby>.xml
```

Mutable artefacts, rebuilt after every publication by `src/summary.py` in the
benchmarks repository. **This is what the site reads.** The site does not parse
the frozen XML: that archive grows without bound and its vocabulary moves with
the schema version, so binding the pages to it would mean a broken site every
time the schema is raised. The XML is what the pages LINK to, not what they read.

```
outputs/status.xml                   the heartbeat, rewritten by every run
outputs/v1/index.json                the map: vocabulary, definitions, zones, files + sha256
outputs/v1/zones.json                per zone: EIC, timezone, currencies, first/last day, count
outputs/v1/scores-latest.csv         one row per zone — the front page
outputs/v1/<ZONE>_scores.csv         the whole history
outputs/v1/<ZONE>_scores-90d.csv     the last 90 delivery days
outputs/v1/<ZONE>_scores-latest.csv  the newest finished delivery day
outputs/v1/forecasts-latest.csv      one row per zone — the newest decision
outputs/v1/<ZONE>_forecasts.csv      every decision, from publication.public_from
outputs/v1/<ZONE>_forecasts-90d.csv  the last 90 delivery days
outputs/v1/<ZONE>_forecasts-latest.csv  the newest decision — normally TOMORROW
```

**Flat, and the underscore is load-bearing.** The separator is `_`, it appears
exactly once, and it separates the zone from the rest. Zone codes carry hyphens
of their own — `DE-LU`, `IT-North` — so `DE-LU_scores-90d.csv` splits on the
first underscore and nothing else needs parsing. A name with NO zone prefix
means every zone. (Owner's call, 2026-09-29, against a first draft with per-zone
folders; the hyphen is what settled it.)

**Three files per series, the ECB's own shape** (owner's call, 2026-09-27): full
history, last 90 days, latest. Whoever wants the series takes the first, whoever
updates daily takes the third, and the 90-day file closes the gap for anyone who
missed a week — which is exactly why we fetch the ECB's 90-day file rather than
its daily one. Nobody has to have the pattern explained.

### The columns, and one real row

```
zone,delivery_day,passive_da_buy_value,passive_da_sell_value,extractable_value,
adverse_value,trailing_bias_value,ptu,ptu_with_action,pass,calc_iteration,
knownby_ts,schema_version,methodology_version,source_file

NL,2026-09-25,-814.3225,-33.8150,391.4750,-1239.6125,-24.6350,96,96,as-known,1,
2026-09-26T09:40:16Z,5,2,nl/2026/09/score_NL_2026-09-25_20260926T094016Z.xml
```

(One line in the file; wrapped here to fit.)

- **One row per zone per delivery day, newest pass only.** This CHANGED on
  2026-09-29: an earlier draft of this brief said both passes. The store keeps
  every version and the summary collapses at read time, so `pass` (`as-known` /
  `as-final`) and `calc_iteration` tell you which one you are looking at. Do not
  build a page that expects two rows for one day.
- **`source_file` is the traceability promise, kept mechanically.** It is the
  path of the frozen document this row came from, relative to the publication
  root. Every number on every page links there; no page needs to explain where a
  figure came from, because the row already says.
- **`ptu` and `ptu_with_action` are not decoration.** The values are SUMS over
  the day, so a short day is mechanically smaller for a reason that has nothing
  to do with the market. Never compare two days without showing both counts.
- **Never assume 96.** A daylight-saving day is 92 or 100 PTU. The expected
  count comes from the day itself; `ptu` is the truth for that row.
- **`index.json` carries the vocabulary**: the five public names, their unit,
  one definition each, and a `sha256` per file. Read the definitions from there
  rather than restating them in page templates — one place, and it travels with
  the data.

### Absences are content, and they are all visible in the columns

The frozen XML says these in its own words (`<no_action>`, `<partial_input
hours=…>`, `<points count="95">`). The site does not read that XML, so here is
the same information as it appears in v1 — each renders as a STATEMENT, never as
a blank or a zero:

| what happened | how the row says it |
|---|---|
| we issued no decision that day | `trailing_bias_value` empty, `ptu_with_action` = 0 |
| some hours were refused for want of whole input | `ptu_with_action` < `ptu` |
| the source skipped a quarter-hour | `ptu` < the day's full count |
| the day is graded, always | the four market values are always present |

A declined or partly declined DECISION is stated in the forecast files, not
here — see Forecasts below.

### Forecasts (in v1 since 2026-10-01)

Same shape as the scores, one row per zone per delivery day, newest
`knownby_ts` wins. The decision is counted in PTU; the action of every PTU is
in the frozen XML that `source_file` names. No hourly profile in the CSV
(owner's call, 2026-10-01).

| column | meaning |
|---|---|
| `zone` | bidding zone code |
| `delivery_day` | the day the decision is FOR, market time |
| `knownby_ts` | when the decision was made; before the gate of the day before |
| `ptu` | PTUs in the delivery day (92 / 96 / 100) |
| `ptu_buy`, `ptu_sell`, `ptu_no_action` | the decision, counted; they sum to `ptu` |
| `data_through` | the freshest fact the signal saw |
| `skip_reason` | empty = the signal did not form; set = REFUSED, and why |
| `schema_version`, `methodology_version` | as of the row |
| `source_file` | the frozen forecast XML |

Three states the site states in words, never as a blank:
decided (`ptu_no_action` = 0), partly decided (0 < `ptu_no_action` < `ptu`),
declined (`ptu_no_action` = `ptu`, `skip_reason` says why — real case: NL
2026-09-17, `input_incomplete:2026-09-13:DA`). A delivery day with NO forecast
row means no forecast was published — either none existed (RO 2026-09-17..27)
or no signal formed on any PTU and nothing was refused, in which case publish
writes no file and v1 has nothing to cite.

The newest row of `<ZONE>_forecasts-latest.csv` is published at ~09:40 UTC,
before the 12:00 auction gate: a public, dated commit made before the prices
exist. That is the one thing no score file can show.

**Versions differ between rows of one file** — NL carries schema 4–5 /
methodology 2, RO 6 / 3. The version belongs to the row, and the CSV keeps
every row whatever its version. What the PAGES do with that is below, under
"Versions on the site".

**Nothing before `publication.public_from`** (2026-09-17) appears in v1,
scores or forecasts. Earlier days are drafts: they stay in `outputs/` on the
server and in the private backup.

### Freshness — two different claims, and they must not be conflated

- **`index.json` → `generated_from`**: the newest `knownby_ts` in the DATA. It
  deliberately contains no wall clock: v1 is a pure function of its inputs, so a
  run that changes nothing writes nothing. This is "data through …".
- **`status.xml` → its own timestamp**: the machine's pulse, rewritten by every
  run including one that changed nothing. This is "last run …".

**The only XML the site parses is `status.xml`**, and only for that heartbeat.
Every number comes from v1.

**The rule that keeps "frozen" meaningful:** everything inside a dated folder is
frozen for ever; everything mutable lives OUTSIDE dated folders and says so on
its own page. Until now the mutable set was exactly one file, deliberately. It
is now a handful, and the line is drawn by path, so a reader can tell from the
URL alone.

Facts the builder must respect:

- **One row per zone per delivery day, newest pass.** `pass` says `as-known`
  or `as-final`; `calc_iteration` counts recalculations of that day from 1 and
  can exceed 2. Never expect two rows for one day.
- **The site never reads the frozen XML** (except `status.xml`). Vocabulary and
  definitions come from `index.json`.
- **Absences are content** — the tables in this section say how each one shows
  in v1. Each renders as a statement, never as a blank or a zero.
- **Four decimals in files; rounded on pages.** Never round a downloadable file.
- **Unit: EUR per 1 MW of trading capacity.** Say it next to every number. It is
  an efficiency yardstick, not a market size — the likeliest misreading.

### Versions on the site (decided 2026-10-01)

- **One version for the whole service, shown once**: in the header of
  `/benchmarks` and in the footer of every page, e.g. "Schema 6 · Methodology 3".
  It is read from `status.xml` → `<version>`. Rows do not repeat it.
- **Pages show only rows of the current methodology.** Values computed under
  different methodologies are NOT comparable. Older rows stay in the CSV for
  download; on the page they are replaced by one sentence, e.g. "Methodology 3
  since 2026-09-26. Earlier days were computed under methodology 2 and are not
  comparable; see News." NOT shown at launch (owner's call, 2026-10-02): with
  no users yet there is nobody to inform. The code is kept (`method_note`).
- **A version change without a News entry fails the build.** The current
  schema and methodology from `status.xml` must each be named by an entry in
  the news source file (format under News below). The owner writes these
  entries; the check makes a silent bump impossible.

## Pages

```
/                     landing
/benchmarks           status + every zone, the last 2-3 delivery days
/docs/                ONE page: #methodology (the nine rules, the five benchmarks,
                      what is NOT claimed) and #data (the data interface)
/docs/methodology     redirect to /docs/#methodology (address kept, 2026-10-02)
/docs/data            redirect to /docs/#data — the report links here, keep it
/docs/report.pdf      the 2020-2026 retrospective
/news                 dated entries, a few sentences each
/about                the project: why it exists, how it is funded, who runs it
/chuchueva            the owner's CV — stable address, indexable
/contact              how to reach her
/support              what it costs, and donations when the rails exist
```

**Landing.** In the first screen without scrolling: what this is in two
sentences; the newest delivery day with its numbers for the live zones; one line
of freshness from `status.xml` (`generated_ts`, `im_through`); and TOMORROW's
decision per zone from `forecasts-latest.csv` — PTU buy / sell / no action and
the time it was published, before the auction gate. That is the one thing no
score can show, so it belongs on the first screen. Below: the two
axes the project measures — how fat a market is (`extractable_value`) and how
much of it a mechanical rule actually takes (`trailing_bias_value`) — and links
to the report and the data.

**Benchmarks.** ONE page for all zones, not a page each. The point of the
project is comparing zones, and a comparison spread over twenty-five pages is
not one. Status block at the top; then the cross-zone table; then per zone a
compact block with the **last two or three delivery days** and a link to each
file. Deep history is a download, not a page — twenty-five zones of series would
be megabytes of HTML for something pandas reads better. Anchors (`#RO`) give a
direct link to a zone without navigation. The list of zones is `zones.json`
and nothing else: a zone in shadow is not published, is not in v1, and the
site does not know about it.

**Docs.** `/docs/data` is what the report's data-interface section points at, and
it must be enough for a stranger to write a parser without writing to us. Its
first line says: files over HTTPS, no query interface.

The report is published as a PDF and **only** as a PDF. Its annual table does not
get a page of its own, before or after publication: the report is a dated, frozen
artefact that can be regenerated and reissued, and a table living on the site
beside it would drift away from it within months.

**News.** Dated, a few sentences per entry, and it is NOT decoration: **every
schema or methodology bump is announced here.** Somebody's parser depends on the
shape, and this is the only honest place to say it changed. Generated from one
small source file (markdown or an HTML fragment) that the owner edits by hand
and the generator wraps in the site template — so the page cannot drift away
from the rest of the site in fonts, palette or layout.

The source is `content/news.md`. One entry = a `##` heading with the ISO date,
then the text. An entry that announces a version carries one line right under
the heading:

```
## 2026-09-26

versions: schema 6, methodology 3

Text of the announcement…
```

The generator reads the `versions:` lines; this is how it knows a version was
announced (see "Versions on the site"). Entries are shown newest first.

**About / Chuchueva / Contact.** `/about` is the project and a short paragraph
about who runs it, linking to `/chuchueva`, which is the CV. One canonical
address each: two URLs for one page split the links and have to be edited twice.
`/contact` carries **`chuchueva@powertradinglab.org`**, an inbound-only address on
the project's own domain, forwarded to the owner's mailbox by Cloudflare Email
Routing (free, and the DNS is already there — active since 2026-09-27). One
name for the page and the address, which is one thing fewer to keep in step. The
point is not protection from
spam — a published address is harvested in the first week and there is no
defence — it is that this address is DISPOSABLE. When it drowns, it is closed,
another is opened, and one line on the site changes; a personal mailbox cannot be
switched off like that. Replies go out from the owner's own mail, which is
acceptable; a sending service is a later purchase and probably never.

Beside it, a link to GitHub: a good share of professional contact arrives that
way and brings no spam. No phone number and no postal address on `/chuchueva` —
those are harvested by people, not robots.

**Support.** IN the first version, as an honest placeholder — and honest means
three things, none of them optional.

*No payment buttons yet.* The owner is opening a business bank account and will
find out from there which rails actually work; Armenia falls out of most
supported-country lists because they run on Stripe, and the realistic ones are
Payoneer and Wise (`HANDOFF.md`, funding). A half-built payment flow is worse
than none: a visitor who clicks and lands nowhere remembers only that. Until
then the page carries text and the contact address.

*No figures yet* (owner's call, 2026-09-27). What the money is for is said in
words — hosting, the domain, and later the compute the harder maths will need —
and the amounts wait until the costs have settled and there is something to
count. The public ledger the project has promised itself starts when the first
coin arrives.

*And the sentence that must never be softened:* **the data is free, complete and
open, always.** Donations pay for hosting and, one day, for the compute the
harder maths will need. They never gate a file and never touch the methodology —
a benchmark's whole value is that nobody paid for its numbers to come out a
particular way.

**The API, asked for on this page and on `/docs/data`.** The honest framing is
not "pay for access". It is: the data is free and complete as files; a query
interface means a second machine and uptime somebody has to be responsible for,
so it exists if someone funds that work — and when it does, it serves the same
numbers, just as freely. The difference between selling access and being paid to
build is the whole difference here.

## How it is built and deployed

**The generator lives in the SITE repository, not in benchmarks** (owner's
question, settled 2026-09-29 — an earlier draft of this brief put
`scripts/make_site.py` in the benchmarks repo, and that was wrong). Three
reasons, in order of weight:

1. The boundary between the two repositories becomes the PUBLISHED CONTRACT
   rather than shared code. That is what `schema_version` exists for: consumers
   are separate from producers. The site is our first consumer, and if it cannot
   live off the public contract, the contract is not good enough. We are about
   to offer that same contract to everyone else.
2. The site's dependencies never reach the machine that must decide before an
   auction gate.
3. The neighbouring session gets a boundary made of a repository instead of a
   rule about which files to touch. It can restyle anything without the physical
   possibility of disturbing the code that computes numbers.

**Nothing is built on the server.** The chain is:

```
server (09:40 and 14:00 UTC)   update → fx → forecast → score → publish
                               → summary → status → push data to the site repo
GitHub Actions (site repo)     reads data/v1 → renders HTML → deploys Pages
```

- The server pushes DATA only, into ONE folder of the site repository,
  `data/`, which it deletes and rebuilds on every push (`src/site_push.py`):
  `outputs/v1/` → `data/v1/`, `outputs/status.xml` → `data/status.xml`, and
  every archive file a v1 row cites → `data/<source_file>`. Archive files no
  row cites — the drafts — are not pushed. `data/` mirrors the publication
  root, so a `source_file` value resolves against it unchanged. Nothing else in
  the site repository is touched, and the site puts nothing into `data/`.
  Live since 2026-10-01 (first push `1f05117`).
  Not `data/raw`, not `logs` — those live in the private backup and must never
  reach a public repository.
- That needs a **write deploy key** on `powertradinglab-site`, generated on the
  server exactly as the backup key was, scoped to that one repository.
- The push is the last step of the run, its failure is counted in the exit code
  and fails nothing else, and the next run pushes the same files again.
- Actions is right for this and wrong for the daily job — the refusal recorded in
  `HOSTING.md` was about running the DATA job there (secrets, punctuality,
  state). Building static pages from committed data has none of those needs.
- **Deploy from the Actions artefact, not by committing HTML.** A workflow that
  commits its own output back to the repository triggers itself. Use
  `actions/upload-pages-artifact` + `actions/deploy-pages`, and the repository
  keeps only data and source.
- No framework, no client libraries, no external fonts. Charts are inline SVG
  produced by the generator: readable with JS off, no third-party script.
- The build is **deterministic** — same inputs, byte-identical output. Same
  discipline as `publish`, and the same test: build twice, diff.
- `powertradinglab.org` is the custom domain; `.com` redirects to it.

## Done means

1. Every number on every page traces to a linked file, and the link works.
2. The site renders correctly with JavaScript disabled.
3. Two consecutive builds from unchanged inputs are byte-identical.
4. Every absence appears as an explicit statement, never as a blank or a
   zero. Real cases in the data: forecast declined — NL 2026-09-17
   (`skip_reason` set, score `ptu_with_action` = 0); hours refused — RO
   2026-09-29 (forecast `ptu_no_action` = 4, score `ptu_with_action` = 92);
   no forecast at all — RO 2026-09-17..28 (no forecast rows); short day — RO
   2026-09-25 (`ptu` = 95).
5. `status.xml` is the only thing claiming to be current, and the landing page
   carries its timestamp.
6. No raw day-ahead price appears anywhere, pages or summary files.
7. Under 200 KB per page, system fonts.
8. Deleting the whole site and rebuilding it loses nothing — no state lives
   only there.
9. The site reads only `data/v1` plus `status.xml` for the heartbeat. If a
   page parses a frozen XML file, the coupling this brief exists to avoid is
   back.

## Decided, 2026-09-27

- **History per zone:** all of it, in the ECB's three-file shape — full, 90 days,
  latest.
- **The report:** PDF only. No annual table on the site.
- **Contact:** `chuchueva@powertradinglab.org`, inbound-only, forwarded by Cloudflare
  Email Routing.
- **Support:** in the first version, as a placeholder. What the money is for in
  words, no amounts yet, no payment buttons until the bank account settles which
  rails work, and the data-is-always-free statement that cannot be softened.

## Decided, 2026-09-29

- **The generator lives in the site repository**, and the boundary between the
  repositories is the published contract.
- **The build runs in GitHub Actions**, never on the server. The server pushes
  data and nothing else.
- **v1 file names are flat**, zone before a single underscore.
- ~~Scores only in this version; forecasts follow later~~ — superseded 2026-10-01.
- **One row per delivery day, newest pass**, with `pass` naming which.

## Decided, 2026-10-01

- **Drafts are cut in the service, not on the site.** `publication.public_from`
  in `settings.json` (2026-09-17) is the first delivery day v1 shows. It is a
  key of its own, separate from `scoring.score_from`, so the two can move
  independently at the PROD cut.
- **The archive is cut with it:** only files a v1 row cites reach the site.
- **The data folder in the site repository is `data/`**, owned by the server.
- **Forecasts are in v1**, by analogy with the scores, counted in PTU.
  This supersedes "forecasts follow later" of 2026-09-29.
- **Versions on the site**: one service version from `status.xml`, shown once;
  pages show only rows of the current methodology; a version without a News
  entry fails the build.
- **Zones come from `zones.json` only.** Shadow is the service's business.
- **The landing page shows tomorrow's decision** from `forecasts-latest.csv`.
- **News source**: `content/news.md`, dated `##` entries, `versions:` line for
  announcements. Written by the owner.

Nothing is open. What is left is building it.
