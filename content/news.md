# News

## 2026-10-05

Today PowerTradingLab goes public. The site publishes five daily short-term trading benchmarks for two bidding zones, 
the Netherlands (NL) and Romania (RO), with data from 17 September 2026. 
The code is open at [github.com/chuchueva/powertradinglab-benchmarks](https://github.com/chuchueva/powertradinglab-benchmarks). 
More zones will follow one at a time. If you are interested in specific zone, write to [chuchueva@powertradinglab.org](mailto:chuchueva@powertradinglab.org).

## 2026-10-03

The report **A Retrospective Look at 2020–2026 Short-Term Power Trading Opportunities in Europe** 
is published on Zenodo: [https://doi.org/10.5281/zenodo.23119533](https://doi.org/10.5281/zenodo.XXXXXXX). 
It covers 25 European bidding zones over 2020–2026. 
The main finding: the *"speculative market fat"* peaked in 2022 on high day-ahead prices, 
two lesser peaks followed in 2024–2025 on volatility, and it has decayed in most zones since the end of 2025. 
All calculations are reproducible against the ENTSO-E archives downloaded on 2 September 2026.

## 2026-09-26

Versions: schema 6, methodology 3.

**Why.** Romania's data for 2026-09-25 had one 15-minute period missing, and
the source never published it. Under the old rule, a single missing period
withdrew the whole day from every forecast whose input window contained it:
three days of decisions lost to one 96th of a day.

**Methodology 3.** The signal is computed per hour of the day, so the input
check now works per hour too. An hour with a gap anywhere in its window gets
no action; every other hour of the day is decided as usual. A whole missing
day still withdraws the whole forecast. Grading changed with it: a day is
graded once it has ended, on the periods it has, and the file states how many
(`ptu`). The same input can now produce a different result, which is why the
methodology number moved.

**Schema 6.** A forecast file can now be partial: it carries the actions for
the hours that were decided, plus one element naming the withdrawn hours and
the missing data behind them. A file with a new element is a new shape, which
is why the schema number moved.

Files published earlier keep their versions and are not re-rendered.