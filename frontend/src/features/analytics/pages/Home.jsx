import { getHome } from "../api/analyticsApi";
import { useEffect, useState } from "react";
import { useTicker } from "../hooks/useTicker";
import ScreenHeader from "../components/ScreenHeader";

const RETURNS = [
  { key: "current_week_return", label: "Week" },
  { key: "current_month_return", label: "Month" },
  { key: "current_quarter_return", label: "Quarter" },
  { key: "current_year_return", label: "Year to date" },
  { key: "trailing_1y_return", label: "1 year" },
  { key: "trailing_3y_return", label: "3 years" },
  { key: "trailing_5y_return", label: "5 years" },
];

function Home() {
  const { ticker } = useTicker();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

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

    const stats = data ?? {};
    const price = stats.current_price;
    const previousClose = stats.previous_close;
    const priceColor = price > previousClose ? "text-chart-green" : price < previousClose ? "text-chart-red" : "text-foreground";

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader
        title="HOME"
        subtitle="Overall information of the asset"
      />
      <div className="bg-card text-gold rounded-lg">
        {error && <p className="text-sm text-destructive">Error: {error}</p>}
        <div className={`text-center self-center p-4 font-semibold ${priceColor}`}> {price} </div>
        {data && RETURNS.map((item) => {
            const value = stats[item.key];
            const color = value > 0 ? "text-chart-green" : value < 0 ? "text-chart-red" : "text-foreground";

            return (
              <div className="p-4" key={item.key}>
                {item.label}: <span className={color}>{value} %</span>
              </div>
            );
            })
        }
      </div>
    </div>
  );
}

export default Home;
