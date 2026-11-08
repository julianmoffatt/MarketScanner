import { getHome, getFundamentals } from "../api/analyticsApi";
import { useEffect, useState } from "react";
import { useTicker } from "../hooks/useTicker";
import ScreenHeader from "../components/ScreenHeader";

const RETURNS = [
  { key: "current_week_return", label: "Week" },
  { key: "current_month_return", label: "Month" },
  { key: "current_quarter_return", label: "Quarter" },
  { key: "current_year_return", label: "YTD" },
  { key: "trailing_3y_return", label: "3 years" },
  { key: "trailing_5y_return", label: "5 years" },
];

// Cada tarjeta de fundamentales: "key" es el grupo que manda el backend y cada fila una metrica.
const FORMATS = {
  ratio: (v) => `${v.toFixed(2)}x`,
  percent: (v) => `${v.toFixed(1)} %`,
  price: (v) => v.toFixed(2),
  count: (v) => String(Math.round(v)),
  money: (v) => {
    const abs = Math.abs(v);
    if (abs >= 1e12) return `${(v / 1e12).toFixed(2)} T`;
    if (abs >= 1e9) return `${(v / 1e9).toFixed(2)} B`;
    if (abs >= 1e6) return `${(v / 1e6).toFixed(2)} M`;
    return v.toFixed(0);
  },
  text: (v) => String(v).replace("_", " "),
};

const FUNDAMENTAL_CARDS = [
  {
    key: "valuation",
    title: "Valuation",
    rows: [
      { key: "market_cap", label: "Market cap", format: "money" },
      { key: "trailing_pe", label: "P/E (trailing)", format: "ratio" },
      { key: "forward_pe", label: "P/E (forward)", format: "ratio" },
      { key: "price_to_sales", label: "P/S", format: "ratio" },
      { key: "ev_to_ebitda", label: "EV/EBITDA", format: "ratio" },
    ],
  },
  {
    key: "profitability",
    title: "Profitability",
    rows: [
      { key: "revenue", label: "Revenue (TTM)", format: "money" },
      { key: "gross_margin", label: "Gross margin", format: "percent" },
      { key: "operating_margin", label: "Operating margin", format: "percent" },
      { key: "net_margin", label: "Net margin", format: "percent" },
      { key: "roe", label: "ROE", format: "percent" },
      { key: "roa", label: "ROA", format: "percent" },
      { key: "debt_to_equity", label: "Debt / equity", format: "ratio", group: "balance_dividend" },
    ],
  },
  {
    key: "growth",
    title: "Growth",
    rows: [
      { key: "revenue_growth", label: "Revenue growth", format: "percent" },
      { key: "earnings_growth", label: "Earnings growth", format: "percent" },
    ],
  },
  {
    key: "analysts",
    title: "Analysts",
    rows: [
      { key: "target_price", label: "Target price", format: "price" },
      { key: "recommendation", label: "Recommendation", format: "text" },
      { key: "analyst_count", label: "Analysts", format: "count" },
    ],
  },
];

// Precios de 10 o mas con 2 decimales; los menores (divisas, centimos) con 4 para no perder precision.
function formatPrice(price) {
  if (price === null || price === undefined) return "–";
  return price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: price >= 10 ? 2 : 4 });
}

function formatValue(value, format) {
  return value === null || value === undefined ? "–" : FORMATS[format](value);
}

function Card({ title, children }) {
  return (
    <section className="rounded-lg bg-card p-4">
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-foreground">{title}</h2>
      {children}
    </section>
  );
}

function Home() {
  const { ticker } = useTicker();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [fundamentals, setFundamentals] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setData(null);
    getHome(ticker)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  // Los fundamentales se piden aparte: Yahoo tarda mas y no debe retrasar el resto de la pantalla.
  useEffect(() => {
    let cancelled = false;
    setFundamentals(null);
    getFundamentals(ticker)
      .then((result) => {
        if (!cancelled) setFundamentals(result);
      })
      .catch(() => {
        if (!cancelled) setFundamentals({ available: false });
      });
    return () => {
      cancelled = true;
    };
  }, [ticker]);

    const stats = data ?? {};
    const price = stats.current_price;

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader
        title="HOME"
        subtitle="Overall information of the asset"
      />
      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      <div className="grid items-start gap-4 md:grid-cols-[18rem_1fr]">
        <Card title="Performance">
          {data && (
            <ul className="divide-y divide-border">
              {RETURNS.map((item) => {
                const value = stats[item.key];
                const color = value > 0 ? "text-chart-green" : value < 0 ? "text-chart-red" : "text-foreground";
                return (
                  <li key={item.key} className="flex items-center justify-between py-2 text-sm text-gold">
                    <span>{item.label}</span>
                    <span className={`tabular-nums ${color}`}>{value} %</span>
                  </li>
                );
              })}
            </ul>
          )}
        </Card>

        <div className="flex flex-col gap-4">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
            {/* Valuation se muestra siempre (el precio sale de Home); el resto solo con fundamentales. */}
            {FUNDAMENTAL_CARDS.filter((card) => card.key === "valuation" || fundamentals?.available).map((card) => (
              <Card key={card.key} title={card.title}>
                <ul className="divide-y divide-border">
                  {card.key === "valuation" && data && (
                    <li className="flex items-center justify-between py-2 text-sm text-gold">
                      <span>Price</span>
                      <span className="tabular-nums text-foreground">{formatPrice(price)}</span>
                    </li>
                  )}
                  {fundamentals?.available &&
                    card.rows.map((row) => (
                      <li key={row.key} className="flex items-center justify-between py-2 text-sm text-gold">
                        <span>{row.label}</span>
                        <span className="tabular-nums text-foreground">
                          {formatValue(fundamentals[row.group ?? card.key]?.[row.key], row.format)}
                        </span>
                      </li>
                    ))}
                </ul>
              </Card>
            ))}
          </div>
          {fundamentals === null && <p className="text-sm text-muted-foreground">Loading fundamentals…</p>}
          {fundamentals && !fundamentals.available && (
            <p className="text-sm text-muted-foreground">
              Fundamentals are only available for individual stocks (not indices, crypto, forex or commodities).
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Home;
