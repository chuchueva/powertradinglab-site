# About

PowerTradingLab is a free and open project on short-term trading in the European power market. 
It publishes a family of short-term trading benchmarks that serve as a reference for human traders and for algorithmic trading systems.

The benchmarks measure a trading result against two major references for a given bidding zone:

- the value the market held: the Extractable Value;
- the result of a simple trailing bias strategy: the Trailing Bias Value.

They play a role similar to the S&P 500 in equity trading: an external, independent reference. [Irina Chuchueva](/chuchueva/), a power market quant, develops and runs the project.

## Benchmarks

For each covered bidding zone, PowerTradingLab computes five benchmarks every day from the day-ahead (DA) and imbalance (IM) prices, per 1 MW of traded quantity.

### Major

- **Extractable Value** — the ceiling: how much value the DA–IM price pair holds; the better side in every quarter-hour, chosen with perfect hindsight.
- **Trailing Bias Value** — the result of a simple trailing bias strategy: the side is chosen from the bias of the three previous days and decided before the DA gate closure. It is the baseline any complex trading model should beat.

### Extra

- **Adverse Value** — the floor: the worse side in every quarter-hour.
- **Passive DA Buy Value** and **Passive DA Sell Value** — one side taken every day, with no foresight; their sign shows which way the DA–IM spread leans.

The method is described on the [Methodology](/methodology/) page, and the files are on the [Data](/data/) page.

The site opens on 5 October 2026 with two zones, the Netherlands (NL) and Romania (RO); their data starts on 17 September 2026. More zones will be added one at a time. 
The retrospective report *A Retrospective Look at 2020–2026 Short-Term Power Trading Opportunities in Europe* covers 25 bidding zones over 2020–2026.

Three rules hold for data publication:

- a published value is never revised silently: each day is scored twice, as first known (the next day) and as final (after the 20th of the following month), and both versions stay public;
- every timestamp is UTC;
- a gap in the source data stays a gap: nothing is filled in or re-estimated as it would be in real trading process.

The price data comes from the ENTSO-E Transparency Platform, the exchange rates from the European Central Bank. 
PowerTradingLab publishes derived results only, not the source price series.
