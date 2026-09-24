import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTicker } from "../hooks/useTicker";
import { getQuarterPatterns } from "../api/analyticsApi";
import ScreenHeader from "../components/ScreenHeader";
import QuarterPatternCard from "../components/QuarterPatternCard";

function QuarterPatterns() {
  const { ticker } = useTicker();
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedQuarter = searchParams.get("quarter") ?? "Q1";

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

  const panels = data?.panels ?? [];
  const panel = panels.find((p) => p.quarter === selectedQuarter);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader
        title="QUARTER COLOR COMBOS · MONTHS"
        subtitle="Which monthly color combination (green/red) is most common within each quarter?"
      >
        <select
          value={selectedQuarter}
          onChange={(e) => setSearchParams({ quarter: e.target.value })}
          className="rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground outline-none focus:border-gold"
        >
          {["Q1", "Q2", "Q3", "Q4"].map((q) => (
            <option key={q} value={q}>
              {q}
            </option>
          ))}
        </select>
      </ScreenHeader>
      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {panel && <QuarterPatternCard panel={panel} />}
    </div>
  );
}

export default QuarterPatterns;
