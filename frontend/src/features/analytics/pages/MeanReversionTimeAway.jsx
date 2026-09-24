import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTicker } from "../hooks/useTicker";
import { getMeanReversion_TimeAway_HT, getMeanReversion_TimeAway_Macro } from "../api/analyticsApi";
import TimeAwayDashboard from "../components/TimeAwayDashboard";

// Igual que Extension to Mean: el modo (ht/macro) vive en ?mode= en vez de
// en la ruta, fusionando las 2 pantallas viejas en una con un selector.
const MODES = [
  { value: "ht", label: "Higher Timeframe (Daily)", fetch: getMeanReversion_TimeAway_HT },
  { value: "macro", label: "Macro (Weekly/Monthly)", fetch: getMeanReversion_TimeAway_Macro },
];

function MeanReversionTimeAway() {
  const { ticker } = useTicker();
  const [searchParams, setSearchParams] = useSearchParams();
  const mode = MODES.find((m) => m.value === searchParams.get("mode")) ?? MODES[0];

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setData(null);
    mode.fetch(ticker)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticker, mode.value]);

  const panels = data?.panels ?? [];

  const modeControl = (
    <select
      value={mode.value}
      onChange={(e) => setSearchParams({ mode: e.target.value })}
      className="rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground outline-none focus:border-gold"
    >
      {MODES.map((m) => (
        <option key={m.value} value={m.value}>
          {m.label}
        </option>
      ))}
    </select>
  );

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {panels.length > 0 && (
        <TimeAwayDashboard
          title="MEAN REVERSION · TIME AWAY"
          subtitle="How long has the price been away from the EMA? · Current vs. historical distribution"
          panels={panels}
          modeControl={modeControl}
        />
      )}
    </div>
  );
}

export default MeanReversionTimeAway;
