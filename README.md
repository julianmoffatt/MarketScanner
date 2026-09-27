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

An ML pipeline predicting next-day candle direction (Green/Red), with results reported transparently:

- Random Forest, XGBoost, and Logistic Regression trained and compared side by side
- Causal, leakage-free feature engineering (expanding-window percentiles, running streaks, no look-ahead)
- `TimeSeriesSplit` cross-validation (not naive K-Fold) over a regularized hyperparameter grid
- Per-model diagnostics: accuracy versus a trivial baseline, train-versus-test overfitting gap, confusion matrix, ROC/AUC, and a calibration (reliability) curve
- A live "predict tomorrow" screen using the same trained pipeline

## Methodology

The project does not claim to beat the market. Across three different model families (linear, bagging, boosting), the measured result is that next-day direction shows no discoverable edge in this feature set (AUC ≈ 0.5). This result is reported directly on screen rather than obscured behind a selectively chosen metric. The emphasis throughout is on methodology:

- Every ML feature is checked for look-ahead bias, validated empirically against the equivalent descriptive-analytics screen
- Non-stationary raw price levels are deliberately excluded from the model — only percentage-based, percentile-based, and relative features are used
- Cross-validation respects chronological order
- Every result is compared against a trivial "always predict the majority class" baseline before being considered an improvement
- Overfitting is actively diagnosed and reduced when found, rather than hidden behind a single headline accuracy figure

## Tech stack

**Backend** — Python 3.11, FastAPI, pandas, scikit-learn, XGBoost, yfinance, Pydantic

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
             FastAPI routes + Pydantic schemas              sklearn Pipeline + GridSearchCV
                          │                                  (TimeSeriesSplit, 3 models)
                          ▼                                                     │
                 React — Statistics tab                    React — Machine Learning tab  ◀──┘
```

## Engineering notes

A few implementation decisions worth calling out beyond the diagram above:

- **Two layers of caching, for two different reasons.** `pipeline.processedTimeframes()` caches parsed OHLCV data per ticker so repeat requests do not re-read CSVs from disk on every call. Separately, the ML pipeline caches the trained models per ticker — training three models with a hyperparameter search can take from a few seconds up to a couple of minutes on tickers with long history, and the Training and Prediction screens share that cache rather than training twice for the same ticker.
- **A caching race condition, identified and resolved.** React's StrictMode double-invokes effects during development; combined with the ML cache, two near-simultaneous requests for a new ticker could both miss the cache and start training in parallel, at one point measured at over 8,000 CPU-seconds consumed within minutes of wall-clock time. The fix is a per-ticker lock: a second concurrent request waits for the first to finish and reuses its result instead of repeating the work.
- **Request cancellation rather than response filtering.** The frontend uses `AbortController` on ticker or screen changes instead of a `cancelled` boolean flag, so the underlying fetch is aborted rather than simply disregarded on arrival — relevant when a request can trigger a multi-minute training run on the backend.
- **A model registry instead of hardcoded model logic.** Adding Logistic Regression as a third model required no changes to the shared training pipeline (`GridSearchCV`, `TimeSeriesSplit`, confusion matrix, ROC, calibration curve). Each model self-registers via a decorator, and the pipeline introspects `model.get_params()` at runtime to determine which hyperparameters and preprocessing steps apply to it.
- **Adaptive handling of limited history instead of a fixed constant.** The warm-up window the ML features require scales down for tickers with shorter histories rather than assuming several years of data are always available, with an explicit floor below which the API returns a clear error instead of training on insufficient data.
- **State lives in the URL, not in component state.** Ticker, analysis mode, and quarter selection are URL or query parameters rather than local `useState`, so every screen is bookmarkable and survives a refresh.
- **One generic component renders most of the Statistics tab.** `PanelGrid` powers seven of the eight Statistics screens through configuration (grouping, column count, an optional per-panel footer render prop) instead of each screen reimplementing its own chart grid.

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

- Single chronological train/test split per ticker — no multi-window walk-forward validation yet
- No formal statistical significance testing between models
- Tickers with fewer than 300 daily candles of history (for example, a stock that IPO'd recently, such as `CRCL` at 288 days) are rejected up front with a clear error rather than being trained on. The warm-up window the ML features require (`SHORT_WINDOW`) scales down for shorter histories, but a floor exists below which a meaningful train/test split is not possible
