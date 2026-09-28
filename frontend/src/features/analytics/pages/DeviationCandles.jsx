import { useEffect, useState } from "react";
import { useTicker } from "../hooks/useTicker";
import { getDeviationCandles } from "../api/analyticsApi";
import PanelGrid from "../components/PanelGrid";
import ScreenHeader from "../components/ScreenHeader";

function DeviationCandles() {
  const { ticker } = useTicker();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setData(null);
    getDeviationCandles(ticker)
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

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader
        title="DEVIATION CANDLES · MAE"
        subtitle="Maximum adverse excursion of green/red candles · Current vs. historical distribution"
      />
      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {panels.length > 0 && <PanelGrid panels={panels} yField="deviation" valueSuffix="%" currentGuideline />}
    </div>
  );
}

export default DeviationCandles;
