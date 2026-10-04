# Irina Chuchueva

::: side
![Irina Chuchueva](/img/chuchueva.jpg){width=450}

**Power Market Quant: forecasting, optimisation, algorithmic trading**
- 
- Happy mother, book lover, musical theater enthusiast, plan my first marathon
- PhD in mathematical modelling 
- Yerevan, Armenia (UTC+4) 
- Remote, contract via registered Individual Entrepreneur



- [chuchueva@powertradinglab.org](mailto:chuchueva@powertradinglab.org)
- [GitHub](https://github.com/chuchueva)
- [LinkedIn](https://www.linkedin.com/in/irinachuchueva/)
- [ORCID](https://orcid.org/0009-0003-0208-5853)
- [Google Scholar](https://scholar.google.com/citations?user=p-AgsYYAAAAJ)
- [Papers, code and worked examples](https://drive.google.com/drive/folders/1XzHRekpXh_9MxMSSggHhN_e3j3_TXcRI)
:::

- 2020–2026: an algorithmic trading project as the sole developer in the European power market, zonal pricing.
- 2007–2020: optimisation and forecasting projects in the Russian power market, nodal (LMP) pricing.
- Over a 19-year career, **all my models and solutions went into production**.

## Experience

### Power trading company, Western Europe — privately owned, name under NDA

**Algorithmic Trading Developer (contract) · June 2020 – May 2026 · remote**

Sole quantitative developer on a six-year project to build an algorithmic trading operation from nothing. Ten algorithms went live in France, the Netherlands and Belgium, covering every short-term trading configuration available in the European market.

- **1. Order Book ↔ Order Book** — LP optimisation over overlapping PH/HH/QH products; stochastic programming version in 2025. Live 2022–23, 2025.
- **2. Order Book ↔ Imbalance** — moving average → dense neural network. Live 2022–25.
- **3. Order Book ↔ Imbalance** — logistic regression → LSTM neural network. Live 2023–24.
- **4. Day-ahead ↔ Order Book ↔ Imbalance** — statistical rules → A2C reinforcement learning. Live 2023–26.
- **5. Order Book ↔ Imbalance** — renewable production forecasting: solar and wind fundamentals. Live 2023.
- **6. Day-ahead ↔ Imbalance** — dense neural network → A2C reinforcement learning. Live 2024–25.
- **7. Order Book ↔ Order Book** — classical spread arbitrage. Live 2025.
- **8. Order Book ↔ Imbalance** — fundamental heuristics, built with traders. Live 2025.
- **9. Order Book ↔ Imbalance** — A2C on the same inputs as #8. Live 2025–26.
- **10. Imbalance ↔ asset control** — solar curtailment algorithm: imbalance price sign forecast, behind-the-meter rooftop solar controlled live in real time; a battery was the intended next step. Live 2025–26.

Overlapping products (PH/HH/QH: hourly, half-hourly, quarter-hourly) are a feature of the European order book.

**How it was delivered**

- Python; each algorithm lived in its own branch of the repository and shipped as its own package, built and deployed to production on Azure.
- Market and operational data were held in PostgreSQL. I specified the ETL: the sources, the update schedules, the backfill rules and what each model needed; the engineering team implemented it.
- Jobs ran on Azure scheduling; alerting and monitoring ran in Azure.
- Every algorithm ran in shadow mode in production before release, which validated the full configuration before any capital was at risk.
- The trading system had no user interface: it was operated from the command line and Azure tooling, with PnL panels in Azure and live and shadow runs traced in plain logs.

### AnalyticsHub LLC

**Load Forecast Developer (contract) · April 2019 – May 2020 · remote**

**Won the load forecast competition that decides who supplies the system.** I developed a load forecast model combining methods from moving averages to neural networks; it won the competition on four consumers across two rounds: September–November 2019 and April–May 2020. The second round began exactly as Russia's lockdown started: the problem was to forecast into a regime with no precedent in the training data. The solution is described in my paper, presented at the **International Symposium on Forecasting 2022, Oxford**.

**How it was delivered**

- Python, shipped as a standalone package in its own repository: one package, one repository, no CI/CD.
- The package exposed its computation through an API: the ETRM system requested the forecasts, drove the schedule and carried the user interface.

### Thomson Reuters (later Refinitiv)

**Senior Analyst, Power Research & Development · July 2015 – November 2018 · Moscow / Oslo / remote**

- Built the Russian power market analysis tool inside the European product line with the Oslo team. Developed **consumption, price and CHP production forecast models**; the price and CHP models were new, built for a market where CHP distorts prices sharply around the heating season.
- **Weather data end to end**: ECMWF, GFS and local providers — delivery schedules, grid formats, interpolation to given coordinates, Kalman filtering to improve quality at a point.
- **Analysed nodal (LMP) price behaviour** by region and supply infrastructure, and the impact of congestion; wrote weekly market price commentary.

**How it was delivered**

- The platform carried dozens of models across the Commodities division: power, carbon, gas, oil. The consumption model alone ran across 50 zones: Europe, Russia, the US, Australia and others. I built and owned the Russian power models inside that European product line.
- MATLAB, as Thomson Reuters internal policy required; each model in its own branch, with production runs configured by hand in the company's internal scheduling tool.
- Reuters ingested the model outputs into its data store and published them to clients through Eikon on a fixed daily schedule.

### Stins Coman Ltd, with IRM Ltd (Vienna)

**Power Analyst · March 2008 – February 2015 · Moscow / Vienna**

- **Combined heat and power plant dispatch optimisation under engineering constraints, 2012–2015.** As lead analyst on the team, I developed optimisation models for seven CHP plants: MILP solved with XPRESS, developed with plant engineering staff, with new gas and steam turbine models built into it. The system entered commercial operation in autumn 2014.
- **ETRM implementation on the IRM platform, 2010–2012.** Russia–Finland cross-border flow optimisation: the two systems are not synchronised, so converter constraints and prices on both sides enter a MILP with a horizon of up to one month.

**How it was delivered**

- A full enterprise implementation for a major market participant: hardware, the complete software stack, customisation of the platform to the client's assets and business processes, and live support through the working days.
- Delivery ran in years, not sprints.

### Wholesale power market operator, Russia

**Power Analyst · May 2007 – January 2008 · Moscow**

Analysis of the cost of day-ahead and imbalance deviations; MATLAB, SAS Macro, SAS Base, SQL. Here I started load forecasting and designed the pattern-analogue model that became my PhD thesis.

## Methods and tools

- **Optimisation**: LP, MILP, stochastic programming; XPRESS, `mip`, Gurobi; asset dispatch under engineering constraints; cross-border scheduling; multi-product position management across hourly, half-hourly and quarter-hourly products.
- **Forecasting**: power price, load and renewable production forecasting; own pattern-analogue method (FMMSP, see Publications); regressions and moving averages; dense and LSTM networks (TensorFlow); A2C reinforcement learning; heuristic rule systems built with traders.
- **Data and systems**: numerical weather prediction feeds (ECMWF, GFS), grid interpolation, Kalman filtering; market data pipelines: ingestion, scheduling and backfill; order book data; latency measurement and reduction in live trading.
- **Markets**: nodal (LMP) and zonal pricing; power market fundamentals for day-ahead, order book and imbalance; Nord Pool and EPEX product structures.
- **Programming**: Python (since 2019), MATLAB (2008–2018), R (2014–2015).
- **Tools**: SQL, SAS, Git, Azure.
- **Languages**: Russian native, English professional, German basic, Armenian studying.

## Publications

Six papers: four in journals, the fifth presented at the International Symposium on Forecasting in 2022. The English translations and the originals are open access.

- *A Retrospective Look at 2020–2026 Short-Term Power Trading Opportunities in Europe*, 2026 · [zenodo.23119533](https://doi.org/10.5281/zenodo.23119533) 
- *The Short-term Electricity Consumption Forecast Competition Under COVID-19 Lockdown Conditions*, 2021 · [zenodo.19604858](https://doi.org/10.5281/zenodo.19604858)
- *The Three-Headed Dragon: Electricity, Trading, Analysis* · Energo-Info, 2018 · [zenodo.19626342](https://doi.org/10.5281/zenodo.19626342)
- *CHP Cost Allocation Methods: A New Method Based on the Linear Steam Turbine Characteristic Curve* · Science and Education of Bauman MSTU, 2016 · [zenodo.19625869](https://doi.org/10.5281/zenodo.19625869)
- *CHP Plant Operations Optimisation under Wholesale Electricity Market Conditions* · Science and Education of Bauman MSTU, 2015 · [zenodo.21256756](https://doi.org/10.5281/zenodo.21256756)
- *A Time Series Forecast Model Based on the Most Similar Pattern* · Informational Technologies, 2010 · [zenodo.19724620](https://doi.org/10.5281/zenodo.19724620) · [Python notebook](https://www.kaggle.com/code/irinachuchueva/forecast-model-on-the-most-similar-pattern)

## Education

**PhD, mathematical modelling** — Bauman Moscow State Technical University, 2012. Thesis: "A time series forecast model based on the most similar pattern"; the Russian version has been cited more than 200 times.
