import { useEffect, useState } from "react";
import { getChartTheme } from "@/lib/plotlyTheme";
import ScreenHeader from "./ScreenHeader";
import TimeAwaySummary from "./TimeAwaySummary";
import TimeAwayHistogramCard from "./TimeAwayHistogramCard";

// Dropdown de timeframe: en HT solo hay "daily" (una opcion), en Macro hay
// "weekly"/"monthly" -- el orden viene del orden en que aparecen los paneles.
function timeframesOf(panels) {
  return [...new Set(panels.map((p) => p.timeframe))];
}

function TimeAwayDashboard({ title, subtitle, panels, modeControl }) {
  const theme = getChartTheme();
  const timeframes = timeframesOf(panels);
  const [selected, setSelected] = useState(timeframes[0]);

  useEffect(() => {
    if (timeframes.length > 0 && !timeframes.includes(selected)) {
      setSelected(timeframes[0]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [panels]);

  const visiblePanels = panels.filter((p) => p.timeframe === selected);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader title={title} subtitle={subtitle}>
        <div className="flex items-center gap-3">
          {modeControl}
          {timeframes.length > 1 && (
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              Higher timeframe
              <select
                value={selected}
                onChange={(e) => setSelected(e.target.value)}
                className="rounded-md border border-border bg-background px-3 py-1.5 text-sm capitalize text-foreground outline-none focus:border-gold"
              >
                {timeframes.map((tf) => (
                  <option key={tf} value={tf} className="capitalize">
                    {tf.charAt(0).toUpperCase() + tf.slice(1)}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
      </ScreenHeader>

      <div
        className="grid flex-1 gap-4"
        style={{ gridTemplateColumns: `repeat(${Math.max(visiblePanels.length, 1)}, minmax(220px, 1fr))` }}
      >
        {visiblePanels.map((panel) => (
          <TimeAwayHistogramCard key={panel.ema_period} panel={panel} timeframe={selected} theme={theme} />
        ))}
      </div>

      <TimeAwaySummary panels={visiblePanels} theme={theme} />
    </div>
  );
}

export default TimeAwayDashboard;
