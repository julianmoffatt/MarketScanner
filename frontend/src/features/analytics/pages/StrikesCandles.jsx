import { useEffect, useState } from "react";
import { useTicker } from "../hooks/useTicker";
import { getStrikesCandles_HT, getStrikesCandles_LT } from "../api/analyticsApi";
import ScreenHeader from "../components/ScreenHeader";
import StrikeStreakTable from "../components/StrikeStreakTable";

function timeframesOf(panels) {
  return [...new Set(panels.map((p) => p.timeframe))];
}

// Cada grupo de timeframes (lt = 1h/4h, ht = daily/weekly/monthly) se pide por
// separado: si uno falla (ej. no hay datos horarios para el ticker) el otro
// se sigue mostrando, y cada error se indica con su grupo.
function useStrikePanels(fetchPanels, ticker) {
  const [state, setState] = useState({ panels: [], error: null });

  useEffect(() => {
    let cancelled = false;
    setState({ panels: [], error: null });
    fetchPanels(ticker)
      .then((result) => {
        if (!cancelled) setState({ panels: result.panels ?? [], error: null });
      })
      .catch((err) => {
        if (!cancelled) setState({ panels: [], error: err.message });
      });
    return () => {
      cancelled = true;
    };
  }, [fetchPanels, ticker]);

  return state;
}

// Una sola cuadricula en vez de una columna apilada por timeframe: asi todas
// las tablas Green quedan en la misma fila y todas las Red en la siguiente,
// con la misma altura, aunque cada timeframe tenga un numero distinto de
// longitudes de racha.
function StrikesGrid({ timeframes, panels }) {
  const panelOf = (timeframe, type) => panels.find((p) => p.timeframe === timeframe && p.type === type);

  return (
    <div
      className="grid flex-1 content-start gap-x-4 gap-y-3"
      style={{ gridTemplateColumns: `repeat(${timeframes.length}, minmax(0, 1fr))` }}
    >
      {timeframes.map((tf) => (
        <div
          key={`${tf}-title`}
          className="text-center text-sm font-semibold uppercase tracking-wide text-muted-foreground"
        >
          {tf}
        </div>
      ))}
      {["Green", "Red"].flatMap((type) =>
        timeframes.map((tf) => {
          const panel = panelOf(tf, type);
          return panel ? <StrikeStreakTable key={`${tf}-${type}`} panel={panel} /> : <div key={`${tf}-${type}`} />;
        }),
      )}
    </div>
  );
}

function StrikesCandles() {
  const { ticker } = useTicker();
  const lower = useStrikePanels(getStrikesCandles_LT, ticker);
  const higher = useStrikePanels(getStrikesCandles_HT, ticker);

  // de menor a mayor timeframe: 1h, 4h, daily, weekly, monthly
  const panels = [...lower.panels, ...higher.panels];
  const timeframes = timeframesOf(panels);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader
        title="STRIKES · CANDLE STREAKS"
        subtitle="How long do green/red streaks typically run? · Ranked by frequency"
      />
      {lower.error && <p className="text-sm text-destructive">Error (1h/4h): {lower.error}</p>}
      {higher.error && <p className="text-sm text-destructive">Error (daily/weekly/monthly): {higher.error}</p>}
      {timeframes.length > 0 && <StrikesGrid timeframes={timeframes} panels={panels} />}
    </div>
  );
}

export default StrikesCandles;
