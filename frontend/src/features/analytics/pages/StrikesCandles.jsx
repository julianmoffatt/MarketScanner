import { useEffect, useState } from "react";
import { useTicker } from "../hooks/useTicker";
import { getStrikesCandles } from "../api/analyticsApi";
import ScreenHeader from "../components/ScreenHeader";
import StrikeStreakTable from "../components/StrikeStreakTable";

function timeframesOf(panels) {
  return [...new Set(panels.map((p) => p.timeframe))];
}

function TimeframeColumn({ timeframe, panels }) {
  const greenPanel = panels.find((p) => p.type === "Green");
  const redPanel = panels.find((p) => p.type === "Red");

  return (
    <div className="flex flex-col gap-3">
      <div className="text-center text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        {timeframe}
      </div>
      {greenPanel && <StrikeStreakTable panel={greenPanel} />}
      {redPanel && <StrikeStreakTable panel={redPanel} />}
    </div>
  );
}

function StrikesCandles() {
  const { ticker } = useTicker();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setData(null);
    getStrikesCandles(ticker)
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

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader
        title="STRIKES · CANDLE STREAKS"
        subtitle="How long do green/red streaks typically run? · Ranked by frequency"
      />
      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {timeframes.length > 0 && (
        <div
          className="grid flex-1 gap-4"
          style={{ gridTemplateColumns: `repeat(${timeframes.length}, minmax(0, 1fr))` }}
        >
          {timeframes.map((tf) => (
            <TimeframeColumn key={tf} timeframe={tf} panels={panels.filter((p) => p.timeframe === tf)} />
          ))}
        </div>
      )}
    </div>
  );
}

export default StrikesCandles;
