import { useState } from "react";
import ScreenHeader from "@/features/analytics/components/ScreenHeader";
import { runBacktest } from "../api/backtestingApi";
import EquityChart from "../components/EquityChart";
import MetricsTable from "../components/MetricsTable";

const STRATEGIES = [
  { value: "mean_reversion_distance", label: "Mean reversion (distance)" },
  { value: "buy_and_hold", label: "Buy & Hold" },
];

const CONFIG_FIELDS = [
  { name: "starting_capital", label: "Starting capital", placeholder: "5000" },
  { name: "initial_exposure", label: "Initial exposure (0-1)", placeholder: "0.5" },
  { name: "window_years", label: "Window (years)", placeholder: "5" },
  { name: "fee", label: "Fee per order", placeholder: "0.25" },
  { name: "spread", label: "Spread", placeholder: "0.001" },
  { name: "periods_per_year", label: "Periods per year", placeholder: "252" },
  { name: "risk_free_rate", label: "Risk-free rate", placeholder: "0" },
];

const EMPTY_CONFIG = Object.fromEntries(CONFIG_FIELDS.map((f) => [f.name, ""]));

const INPUT_CLASS =
  "w-full rounded-md border border-border bg-card px-3 py-1.5 text-sm text-foreground outline-none focus:border-gold";

function buildRequest(tickersText, strategy, config) {
  const tickers = tickersText.split(/[\s,]+/).filter(Boolean);
  if (tickers.length === 0) throw new Error("Enter at least one ticker");

  const parsed = {};
  for (const field of CONFIG_FIELDS) {
    const raw = config[field.name].trim();
    if (raw === "") continue;
    const value = Number(raw);
    if (Number.isNaN(value)) throw new Error(`${field.label} must be a number`);
    parsed[field.name] = value;
  }
  return { tickers, strategy, config: parsed };
}

function Field({ label, children }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}

function Backtesting() {
  const [tickers, setTickers] = useState("");
  const [strategy, setStrategy] = useState(STRATEGIES[0].value);
  const [config, setConfig] = useState(EMPTY_CONFIG);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    let request;
    try {
      request = buildRequest(tickers, strategy, config);
    } catch (err) {
      setError(err.message);
      return;
    }

    setLoading(true);
    try {
      setResult(await runBacktest(request));
    } catch (err) {
      setResult(null);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 px-6 py-3">
      <ScreenHeader
        title="BACKTESTING"
        subtitle="Run a strategy against Buy & Hold. Blank parameters use the defaults."
      />

      <form onSubmit={handleSubmit} className="rounded-lg border border-border bg-card p-4">
        <div className="grid gap-3 md:grid-cols-2">
          <Field label="Tickers (separated by commas)">
            <input
              value={tickers}
              onChange={(e) => setTickers(e.target.value)}
              placeholder="SP500, AAPL"
              className={INPUT_CLASS}
            />
          </Field>
          <Field label="Strategy">
            <select value={strategy} onChange={(e) => setStrategy(e.target.value)} className={INPUT_CLASS}>
              {STRATEGIES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </Field>
        </div>

        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {CONFIG_FIELDS.map((field) => (
            <Field key={field.name} label={field.label}>
              <input
                value={config[field.name]}
                onChange={(e) => setConfig({ ...config, [field.name]: e.target.value })}
                placeholder={field.placeholder}
                inputMode="decimal"
                className={INPUT_CLASS}
              />
            </Field>
          ))}
        </div>

        <div className="mt-4 flex items-center gap-4">
          <button
            type="submit"
            disabled={loading}
            className="rounded-md border border-gold px-4 py-1.5 text-sm font-medium text-gold transition-colors hover:bg-gold hover:text-background disabled:opacity-50"
          >
            {loading ? "Running..." : "Execute backtesting"}
          </button>
          {error && <p className="text-sm text-destructive">Error: {error}</p>}
        </div>
      </form>

      {result && (
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-lg border border-border bg-card p-4 lg:col-span-2">
            <div className="mb-2 text-xs font-medium text-muted-foreground">
              Equity curve · {result.tickers.join(", ")} · {result.strategy.replace(/_/g, " ")}
            </div>
            <EquityChart equity={result.equity} benchmark={result.benchmark_equity} />
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="mb-2 text-xs font-medium text-muted-foreground">Metrics</div>
            <MetricsTable metrics={result.metrics} benchmarkMetrics={result.benchmark_metrics} />
          </div>
        </div>
      )}
    </div>
  );
}

export default Backtesting;
