import { useEffect, useState } from "react";
import { useTicker } from "../hooks/useTicker";
import { getRsi } from "../api/analyticsApi";
import ScreenHeader from "../components/ScreenHeader";
import PanelGrid from "../components/PanelGrid";
import RsiRankingTables from "../components/RsiRankingTables";

function Rsi() {
  const { ticker } = useTicker();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setData(null);
    getRsi(ticker)
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
        title="RSI · DISTRIBUTION"
        subtitle="Where does the current RSI sit vs. its own historical distribution?"
      />
      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {panels.length > 0 && (
        <PanelGrid
          panels={panels}
          yField="rsi_value"
          groupBy={() => "all"}
          panelFooter={(panel) => <RsiRankingTables panel={panel} />}
        />
      )}
    </div>
  );
}

export default Rsi;
