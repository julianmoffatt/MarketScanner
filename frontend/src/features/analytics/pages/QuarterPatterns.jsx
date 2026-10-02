import { useEffect, useState } from "react";
import { useTicker } from "../hooks/useTicker";
import { getQuarterPatterns } from "../api/analyticsApi";
import ScreenHeader from "../components/ScreenHeader";
import QuarterPatternCard from "../components/QuarterPatternCard";

const QUARTER_ORDER = ["Q1", "Q2", "Q3", "Q4"];

// Junta los 8 patrones de los 4 quarters en una sola distribucion general --
// suma los counts (numeros absolutos, no los pct ya redondeados de cada
// quarter) y recalcula el pct sobre el total combinado, para ver que
// combinacion domina en el año completo en vez de por trimestre.
function buildOverallPanel(panels) {
  const totals = new Map();
  let totalOccurrences = 0;

  for (const panel of panels) {
    totalOccurrences += panel.occurrences;
    for (const row of panel.rows) {
      totals.set(row.pattern, (totals.get(row.pattern) ?? 0) + row.count);
    }
  }

  // is_current se queda en false a proposito -- eso es lo que mantiene el
  // coloreado por patron (verde/rojo) en las barras en vez del dorado/gris
  // de "posible/eliminado" de un trimestre concreto. Pero el trimestre
  // actual SI existe siempre (uno de los 4 paneles lo es), asi que "Current
  // (partial)"/"Still possible" y que patrones siguen siendo "Possible" se
  // copian de ese panel via has_current_quarter/possiblePatterns,
  // independiente de is_current.
  const current = panels.find((p) => p.is_current);
  const possiblePatterns = new Set(current?.rows.filter((r) => r.is_possible).map((r) => r.pattern) ?? []);

  const rows = [...totals.entries()]
    .map(([pattern, count]) => ({
      pattern,
      count,
      pct: totalOccurrences ? (count / totalOccurrences) * 100 : 0,
      is_possible: possiblePatterns.has(pattern),
    }))
    .sort((a, b) => b.count - a.count);

  return {
    quarter: "All Quarters",
    is_current: false,
    has_current_quarter: Boolean(current),
    current_prefix: current?.current_prefix ?? "",
    occurrences: totalOccurrences,
    still_possible: current?.still_possible ?? 0,
    rows,
  };
}

function QuarterPatterns() {
  const { ticker } = useTicker();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setData(null);
    getQuarterPatterns(ticker)
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

  const panels = [...(data?.panels ?? [])].sort(
    (a, b) => QUARTER_ORDER.indexOf(a.quarter) - QUARTER_ORDER.indexOf(b.quarter)
  );

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader
        title="QUARTER COLOR COMBOS · MONTHS"
        subtitle="Which monthly color combination (green/red) is most common within each quarter?"
      />
      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {panels.length > 0 && (
        <div className="flex flex-col gap-4">
          <QuarterPatternCard panel={buildOverallPanel(panels)} />
          {panels.map((panel) => (
            <QuarterPatternCard key={panel.quarter} panel={panel} />
          ))}
        </div>
      )}
    </div>
  );
}

export default QuarterPatterns;
