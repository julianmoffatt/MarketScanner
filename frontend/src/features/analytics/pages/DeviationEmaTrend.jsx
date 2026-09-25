import { useEffect, useState } from "react";
import { useTicker } from "../hooks/useTicker";
import { getDeviationEmaTrend } from "../api/analyticsApi";
import PanelGrid from "../components/PanelGrid";
import ScreenHeader from "../components/ScreenHeader";
import DeviationForwardReturnRankings from "../components/DeviationForwardReturnRankings";

function DeviationEmaTrend() {
  const { ticker } = useTicker();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setData(null);
    getDeviationEmaTrend(ticker)
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
        title="DEVIATION EMA TREND · ABSORPTION / REJECTION"
        subtitle="How far does price push through the EMA before reversing? · Historical distribution by pattern"
      />
      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {panels.length > 0 && (
        <PanelGrid
          panels={panels}
          yField="deviation"
          valueSuffix="%"
          columnsPerRow={2}
          groupBy={(panel) => panel.type}
          currentField={null}
          footerLayout="row"
          showPercentile={false}
          panelFooter={(panel) => <DeviationForwardReturnRankings panel={panel} />}
        />
      )}
    </div>
  );
}

export default DeviationEmaTrend;
