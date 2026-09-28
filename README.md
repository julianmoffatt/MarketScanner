# Market Scanner

A full-stack quantitative market analytics platform: a Python/FastAPI backend that ingests and analyzes price data for stocks, crypto, and other assets, paired with a React frontend for exploring the results — plus a machine learning pipeline built with the same rigor a quant research process demands.

Built as a portfolio project to demonstrate end-to-end skills across data engineering, statistical analysis, and applied machine learning.

## What it does

### Statistics screens

Descriptive, historical analysis of price behavior for any ticker:

- **Distance to Mean** — how far price is extended from the EMA, across timeframes
- **Time Away from Mean** — how long price has stayed outside a volatility-adjusted band around the EMA
- **Trend Duration** — consecutive days spent above/below the EMA
- **Strikes** — consecutive green/red candle streaks
- **RSI** — historical distribution, percentile, and top/bottom RSI readings
- **Deviation Candles** — Maximum Adverse Excursion (MAE) per candle: how far price moved against the eventual close before it happened (e.g., how far a green candle dipped below its open before recovering to close higher)
- **Deviation Trend** — Absorption vs. Rejection patterns around the EMA, with forward-return rankings (how price performed 1/3/5 periods after each occurrence)
- **Quarter Patterns** — which monthly Green/Red color combination is most common within each quarter, and which are still statistically possible for the current quarter

### Machine Learning screens

An ML pipeline predicting next-week candle direction (Green/Red) on weekly candles, with results reported transparently:

- Random Forest, XGBoost, and Logistic Regression trained and compared side by side
- Causal, leakage-free feature engineering: expanding-window percentiles, running streaks at multiple horizons (weekly, monthly, quarterly, yearly), distance to the prior year's high/low, EMA-extension and time-away-from-mean percentiles, and shared macro context (10-year/3-month Treasury yield percentiles and their spread) — all validated to carry no look-ahead
- Fixed, shared hyperparameters across the whole ticker universe instead of a per-ticker grid search — chosen to regularize model complexity, validated via controlled ablation across a representative sample of tickers, and reused everywhere to avoid overfitting the search itself and to keep training feasible across hundreds of tickers
- Walk-forward evaluation (expanding-window, chronological folds) instead of a single train/test split — every result on screen is pooled across folds rather than measured on one fixed tail of history
- Per-model diagnostics: accuracy versus a trivial baseline, train-versus-test overfitting gap, confusion matrix, ROC/AUC, and a calibration (reliability) curve
- A live "predict next week" screen using the same trained pipeline

## Methodology

This is the part of the project under the most active iteration. The feature set, model configuration, and evaluation approach are still evolving as new candidates are tested and either kept or discarded:

- Every ML feature is checked for look-ahead bias before being added, and validated empirically against the equivalent descriptive-analytics screen where one exists
- Non-stationary raw price levels are deliberately excluded from the model — only percentage-based, percentile-based, and relative features are used
- New features are evaluated through controlled ablation testing — same tickers, same model configuration, with and without the candidate feature — across a representative multi-asset universe (indices, commodities, forex) before being adopted
- Hyperparameters are fixed and shared across the ticker universe rather than searched per ticker, and are themselves periodically re-validated the same way — via controlled ablation across a representative universe — rather than tuned to any single asset
- Evaluation uses walk-forward validation rather than a single train/test split: each fold trains on all history up to that point and is scored only on the following, unseen period, with an initial anchor window ensuring every fold has enough history behind it before being evaluated at all
- The model used for live predictions is retrained on the full available history once the walk-forward evaluation is complete — the evaluation and the deployed model are deliberately not the same fit
- Every result is compared against a trivial "always predict the majority class" baseline before any apparent improvement is considered
- Overfitting is actively diagnosed (train-versus-test gap) and reduced when found, rather than hidden behind a single headline accuracy figure

## Tech stack

**Backend** — Python 3.11, FastAPI, pandas, scikit-learn, XGBoost, SciPy, yfinance, Pydantic

**Frontend** — React 19, Vite, React Router, Tailwind CSS 4, shadcn/ui, Plotly.js

## Architecture

```
yfinance ──▶ ingestion / preprocessing ──▶ build_features.py (EMAs, RSI, returns, volatility)
                                                     │
                          ┌──────────────────────────┴──────────────────────────┐
                          ▼                                                     ▼
              analysis/*.py                                        build_features_ML.py
        (one module per Statistics screen)                    (causal, non-look-ahead features)
                          │                                                     │
                          ▼                                                     ▼
             FastAPI routes + Pydantic schemas              sklearn Pipeline, walk-forward,
                          │                                  fixed hyperparameters (3 models)
                          ▼                                                     │
                 React — Statistics tab                    React — Machine Learning tab  ◀──┘
```

## Engineering notes

A few implementation decisions worth calling out beyond the diagram above:

- **Two layers of caching, for two different reasons.** `pipeline.processedTimeframes()` caches parsed OHLCV data per ticker so repeat requests do not re-read CSVs from disk on every call. Separately, the ML pipeline caches the trained models per ticker — walk-forward means several fits per model instead of one, so training three models can take a few seconds to a bit longer on tickers with long history, and the Training and Prediction screens share that cache rather than training twice for the same ticker.
- **A caching race condition, identified and resolved.** React's StrictMode double-invokes effects during development; combined with the ML cache, two near-simultaneous requests for a new ticker could both miss the cache and start training in parallel, at one point measured at over 8,000 CPU-seconds consumed within minutes of wall-clock time. The fix is a per-ticker lock: a second concurrent request waits for the first to finish and reuses its result instead of repeating the work.
- **Request cancellation rather than response filtering.** The frontend uses `AbortController` on ticker or screen changes instead of a `cancelled` boolean flag, so the underlying fetch is aborted rather than simply disregarded on arrival — relevant when a request can trigger a multi-minute training run on the backend.
- **A model registry instead of hardcoded model logic.** Adding Logistic Regression as a third model required no changes to the shared training pipeline (train/test split, confusion matrix, ROC, calibration curve). Each model self-registers via a decorator, and the pipeline introspects `model.get_params()` at runtime to determine which hyperparameters and preprocessing steps apply to it.
- **Adaptive handling of limited history instead of a fixed constant.** The warm-up window the ML features require, and the walk-forward anchor/fold sizing built on top of it, both scale down for tickers with shorter histories rather than assuming several years of data are always available, with an explicit floor below which the API returns a clear error instead of training on insufficient data.
- **State lives in the URL, not in component state.** Ticker, analysis mode, and quarter selection are URL or query parameters rather than local `useState`, so every screen is bookmarkable and survives a refresh.
- **One generic component renders most of the Statistics tab.** `PanelGrid` powers seven of the eight Statistics screens through configuration (grouping, column count, an optional per-panel footer render prop) instead of each screen reimplementing its own chart grid.

## Project structure

```
backend/
  src/market_platform/
    data/          # ingestion + preprocessing
    features/      # build_features.py (descriptive), build_features_ML.py (causal ML features)
    analysis/      # one module per Statistics screen
    ML/            # model registry, training pipeline, results
    api/           # FastAPI routes + Pydantic schemas
    services/      # thin glue between routes and analysis/ML
frontend/
  src/
    features/analytics/  # Statistics screens
    features/ml/          # Machine Learning screens
    layouts/               # shared nav/header
```

## Known limitations

- Statistical significance checks (bootstrap confidence intervals, correction for testing many tickers/models at once) are currently run as ad hoc research analysis rather than as an automated step inside the training pipeline itself
- Walk-forward fold count and window sizing are adaptive but fairly coarse-grained for shorter-history tickers, trading finer regime coverage for larger, more statistically stable folds
- Tickers with fewer than 300 weekly candles of history are rejected up front with a clear error rather than being trained on. The warm-up window the ML features require (`SHORT_WINDOW`) scales down for shorter histories, but a floor exists below which a meaningful train/test split is not possible

## Getting started

Requires **Python 3.11** and **Node.js**.

```bash
git clone https://github.com/julianmoffatt/MarketScanner.git
cd MarketScanner
pip install -r backend/requirements.txt
npm install
npm install --prefix frontend
npm run dev
```

`npm run dev` starts the FastAPI backend (`localhost:8000`) and the Vite frontend (`localhost:5173`) together. Open `http://localhost:5173`.

> On macOS/Linux, replace the Windows-specific `py -3.11` inside `package.json`'s `dev` script with `python3.11` if needed.
