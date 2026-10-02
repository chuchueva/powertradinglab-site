## How the files are organised

**Two kinds of file.** The service writes one XML
file per zone, per delivery day and per pass, carrying every 15-minute period
(PTU) and the parameters the numbers were computed under:

    <zone>/YYYY/MM/forecast_<ZONE>_<delivery day>_<computed at>.xml
    <zone>/YYYY/MM/score_<ZONE>_<delivery day>_<computed at>.xml

The service never rewrites a published file. A correction arrives as a new file
beside the old one. Two other things change: `v1/`, the reader's shape of the
same numbers, rebuilt after every run, and `status.xml`, which says when the
service last ran and what it found.

**Names.** The zone comes first, followed by exactly one underscore:
`NL_scores.csv`, `DE-LU_scores-90d.csv`. Zone codes contain hyphens of their
own, so splitting on the first underscore is the whole parser. A name with no
zone prefix (`scores-latest.csv`) covers every zone. `index.json` lists every
file with its size and SHA-256, and `zones.json` describes each zone.

**Three files per zone**, the shape similar to ECB uses for exchange rates:
`<ZONE>_scores.csv` holds the full history, `-90d` the last 90 delivery days,
`-latest` the newest day. Take the full file once, then the latest file daily;
after missing a few weeks, take the 90-day file. Forecasts follow the same
pattern. Each forecast file's latest row is normally tomorrow's decision,
published before the 12:00 day-ahead gate, in particular at 9:40-9:45 UTC.

**Passes.** The service scores a delivery day twice. The as-known pass runs the
morning after delivery, once imbalance prices are complete. The as-final pass
runs after the 20th of the following month, once the TSO has settled. `v1`
shows the newest pass per day, and the `pass` and `calc_iteration` columns say
which one it is. The archive keeps both.

**Versions belong to the row.** `schema_version` changes when the shape of a
file changes; `methodology_version` changes when the same input could produce
a different number. Each row carries the two numbers in force when the service
computed it, so one file can hold several versions. The service never
re-renders history under a newer version.

**Absences are visible.**
- An empty cell means no value, and it never means zero.
- `trailing_bias_value` is empty on a day with no decision.
- `ptu` below the day's full count (92, 96 or 100) means the source published
  fewer PTU prices.
- `ptu_with_action` gives the number for our forecast result.
- In forecasts, `ptu_no_action` counts the undecided periods. `skip_reason`
  separates a refused forecast (input day incomplete) from a signal that did
  not form.
- A delivery day with no forecast row means the service published no forecast
  for it.

All timestamps are UTC (`…Z`); `delivery_day` is in the zone's own market time.
Every row names its archive file in `source_file`. The files carry derived
values only, never a day-ahead or imbalance price. The series start on
2026-09-17.

## A query interface

The files are the interface, and they are complete: every number the site
shows, the full history, free, under the same terms. Any language reads a CSV,
and a scheduled download of one `-latest` file per zone keeps a copy current.

There is no API. A Python package for reading these files is in development.