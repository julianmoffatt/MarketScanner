# Market Scanner | Advanced Market Statistics

Full-Stack Quantitative Market Analytics Platform — Developer & Researcher

A Python/FastAPI + React platform that ingests and analyzes historical price data across any asset class, combining an advanced market-statistics engine (trend behavior, mean-reversion probability, maximum adverse excursion, streak analysis) with an end-to-end machine learning pipeline to support data-driven investment research.

Originally developed as a personal quantitative research project, now partially opened to the public as a portfolio project, with selected features and proprietary components restricted. The project demonstrates end-to-end skills across data engineering, statistical analysis, and applied machine learning.

## What it does

### Statistics screens

Descriptive, historical analysis of price behavior for any ticker:

- **Distance to Mean** — how far price is extended from the EMA, across timeframes
- **Time Away from Mean** — how long price has stayed outside a volatility-adjusted band around the EMA
- **Trend Duration** — consecutive days spent above/below the EMA
- **Strikes** — consecutive green/red candle streaks
- **RSI** — historical distribution, percentile, and top/bottom RSI readings
- **MAE (Candles)** — Maximum Adverse Excursion (MAE) per candle: how far price moved against the eventual close before it happened (e.g., how far a green candle dipped below its open before recovering to close higher)
- **MAE (EMA Trend)** — Absorption vs. Rejection patterns around the EMA, with forward-return rankings (how price performed 1/3/5 periods after each occurrence)
- **Quarter Patterns** — which monthly Green/Red color combination is most common within each quarter, and which are still statistically possible for the current quarter

<img width="1917" height="857" alt="extension" src="https://github.com/user-attachments/assets/6858be69-919f-41e9-9d1b-e22547bdc01d" />
<img width="1897" height="861" alt="MAE (trend)" src="https://github.com/user-attachments/assets/baf10f75-286d-4e1a-bf76-9fa03cae3413" />
<img width="1917" height="861" alt="rsi" src="https://github.com/user-attachments/assets/179a613b-c7bd-48a2-adf8-0f60a56db22f" />
<img width="1896" height="841" alt="quarter patterns" src="https://github.com/user-attachments/assets/9070c85c-2433-4ccc-ba9f-ffef1c1a93d5" />
<img width="1896" height="860" alt="ML" src="https://github.com/user-attachments/assets/e6a9f409-5548-46db-81bb-94a6a5d18d50" />

### Machine Learning screens

An ML pipeline predicting next-week candle direction (Green/Red) on weekly candles, with results reported transparently:

- Random Forest, XGBoost, and Logistic Regression trained and compared side by side
- Causal, leakage-free feature engineering: expanding-window percentiles, running streaks at multiple horizons (weekly, monthly, quarterly, yearly), distance to the prior year's high/low, EMA-extension and time-away-from-mean percentiles, and shared macro context (10-year/3-month Treasury yield percentiles and their spread) — all validated to carry no look-ahead
- Fixed, shared hyperparameters across the whole ticker universe instead of a per-ticker grid search — chosen to regularize model complexity, reused everywhere to avoid overfitting the search itself and to keep training feasible across hundreds of tickers
- Walk-forward evaluation (expanding-window, chronological folds) instead of a single train/test split
- Per-model diagnostics: accuracy versus a trivial baseline, train-versus-test overfitting gap, confusion matrix, ROC/AUC, and a calibration (reliability) curve
- A live "predict next week" screen using the same trained pipeline

## Methodology

This is the part of the project under the most active iteration. The feature set, model configuration, and evaluation approach are still evolving as new candidates are tested and either kept or discarded:

- Every ML feature is checked for look-ahead bias before being added, and validated empirically against the equivalent descriptive-analytics screen where one exists
- Non-stationary raw price levels are deliberately excluded from the model — only percentage-based, percentile-based, and relative features are used
- New features are evaluated through controlled ablation testing — same tickers, same model configuration, with and without the candidate feature — across a representative multi-asset universe (indices, commodities, forex) before being adopted
- Hyperparameters are fixed and shared across the ticker universe rather than searched per ticker, and are themselves periodically re-validated the same way
- Evaluation uses walk-forward validation rather than a single train/test split: each fold trains on all history up to that point and is scored only on the following, unseen period, with an initial anchor window ensuring every fold has enough history behind it before being evaluated at all
- The model used for live predictions is retrained on the full available history once the walk-forward evaluation is complete — the evaluation and the deployed model are deliberately not the same fit
- Every result is compared against a trivial "always predict the majority class" baseline before any apparent improvement is considered
- Overfitting is actively diagnosed (train-versus-test gap) and reduced when found

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

- **Two layers of caching.** `pipeline.processedTimeframes()` caches parsed OHLCV data per ticker so repeat requests do not re-read CSVs from disk on every call. Separately, the ML pipeline caches the trained models per ticker — walk-forward means several fits per model instead of one, so training three models can take a few seconds to a bit longer on tickers with long history, and the Training and Prediction screens share that cache rather than training twice for the same ticker.
- **A model registry instead of hardcoded model logic.** Adding Logistic Regression as a third model required no changes to the shared training pipeline (train/test split, confusion matrix, ROC, calibration curve). Each model self-registers via a decorator, and the pipeline introspects `model.get_params()` at runtime to determine which hyperparameters and preprocessing steps apply to it.

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
