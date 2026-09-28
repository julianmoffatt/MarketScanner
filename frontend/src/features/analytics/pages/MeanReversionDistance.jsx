import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTicker } from "../hooks/useTicker";
import {
  getMeanReversion_Distance_LT,
  getMeanReversion_Distance_HT,
  getMeanReversion_Distance_Macro,
} from "../api/analyticsApi";
import ScreenHeader from "../components/ScreenHeader";
import PanelGrid from "../components/PanelGrid";
import { getChartTheme } from "@/lib/plotlyTheme";

// El modo (lt/ht/macro) vive en la query string (?mode=) en vez de en la
// ruta -- asi la seleccion es bookmarkeable/persiste al recargar, y las 3
// pantallas viejas se fusionan en una sola con un selector.
const MODES = [
  {
    value: "lt",
    label: "Lower Timeframe (1h/4h)",
    fetch: getMeanReversion_Distance_LT,
    subtitle: "How far is price extended from the EMA on 1h/4h? · Current vs. historical distribution",
  },
  {
    value: "ht",
    label: "Higher Timeframe (Daily/Weekly)",
    fetch: getMeanReversion_Distance_HT,
    subtitle: "How far is price extended from the EMA on daily/weekly? · Current vs. historical distribution",
  },
  {
    value: "macro",
    label: "Macro (Slow EMA)",
    fetch: getMeanReversion_Distance_Macro,
    subtitle: "How far is price extended from the slow EMA on daily/weekly? · Current vs. historical distribution",
  },
];

function MeanReversionDistance() {
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

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader title="MEAN REVERSION · DISTANCE" subtitle={mode.subtitle}>
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
      </ScreenHeader>
      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {panels.length > 0 && (
        <PanelGrid
          panels={panels}
          yField="extension_to_mean"
          valueSuffix="%"
          currentGuideline
          currentColor={getChartTheme().highlightLight}
          currentTextColor="#ffffff"
          dataColor={getChartTheme().accentDark}
        />
      )}
    </div>
  );
}

export default MeanReversionDistance;
