import { useEffect, useState } from "react";
import { useTicker } from "../hooks/useTicker";
import { getTrendDuration } from "../api/analyticsApi";
import ScreenHeader from "../components/ScreenHeader";
import TrendDurationSection from "../components/TrendDurationSection";

function timeframesOf(panels) {
  return [...new Set(panels.map((p) => p.timeframe))];
}

function TrendDuration() {
  const { ticker } = useTicker();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setData(null);
    getTrendDuration(ticker)
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

  const panels = data?.panels ?? [];
  const timeframes = timeframesOf(panels);

  useEffect(() => {
    if (timeframes.length > 0 && !timeframes.includes(selected)) {
      setSelected(timeframes[0]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [panels]);

  const visiblePanels = panels.filter((p) => p.timeframe === selected);
  const abovePanel = visiblePanels.find((p) => p.type === "Above");
  const belowPanel = visiblePanels.find((p) => p.type === "Below");

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader
        title="TREND DURATION · DAYS"
        subtitle="How many days does the price stay above or below the EMA 10 (± volatility-based tolerance) before changing trend?"
      >
        {timeframes.length > 1 && (
          <select
            value={selected ?? ""}
            onChange={(e) => setSelected(e.target.value)}
            className="rounded-md border border-border bg-background px-3 py-1.5 text-sm capitalize text-foreground outline-none focus:border-gold"
          >
            {timeframes.map((tf) => (
              <option key={tf} value={tf} className="capitalize">
                {tf.charAt(0).toUpperCase() + tf.slice(1)}
              </option>
            ))}
          </select>
        )}
      </ScreenHeader>

      {error && <p className="text-sm text-destructive">Error: {error}</p>}

      {abovePanel && <TrendDurationSection panel={abovePanel} />}
      {belowPanel && <TrendDurationSection panel={belowPanel} />}
    </div>
  );
}

export default TrendDuration;
