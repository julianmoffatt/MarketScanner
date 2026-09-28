import { getEmaColor } from "@/lib/plotlyTheme";

// Fila con la mini-barra de distribucion inline: 1 (min) -- pista con el
// tramo p95 sombreado, la marca punteada de la mediana y el punto del valor
// actual (con su numero encima).
function DistributionCell({ panel, color, theme }) {
  const min = 1;
  const max = Math.max(panel.p95, panel.current_value, panel.median, min + 1);
  const pct = (value) => Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));

  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] text-muted-foreground">{min}</span>
      <div className="relative min-w-[180px] flex-1 pt-4">
        <div
          className="absolute top-0 -translate-x-1/2 whitespace-nowrap text-xs font-bold"
          style={{ left: `${pct(panel.current_value)}%`, color }}
        >
          {panel.current_value}
        </div>
        <div className="relative h-2 rounded-full bg-muted">
          <div
            className="absolute inset-y-0 left-0 rounded-full"
            style={{ width: `${pct(panel.p95)}%`, background: color, opacity: 0.35 }}
          />
          <div
            className="absolute top-1/2 h-3.5 -translate-x-1/2 -translate-y-1/2 border-l border-dashed"
            style={{ left: `${pct(panel.median)}%`, borderColor: theme.text }}
          />
          <div
            className="absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2"
            style={{ left: `${pct(panel.current_value)}%`, background: color, borderColor: theme.paper }}
          />
        </div>
      </div>
    </div>
  );
}

// Tabla unica: antes eran 2 tarjetas separadas (tabla + barra de rango) con
// las mismas EMAs repetidas -- se fusionan en una sola fila por EMA.
function TimeAwaySummary({ panels, theme }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-gold">
            <th className="whitespace-nowrap pb-3 pr-4 font-medium">EMA</th>
            <th className="whitespace-nowrap px-4 pb-3 text-center font-medium">
              Current
              <div className="text-[10px] normal-case text-muted-foreground/70">(candles)</div>
            </th>
            <th className="whitespace-nowrap px-4 pb-3 text-center font-medium">
              Median
              <div className="text-[10px] normal-case text-muted-foreground/70">(candles)</div>
            </th>
            <th className="pb-3 pl-4 font-medium">Distribution</th>
            <th className="whitespace-nowrap pb-3 pl-6 text-right font-medium">P95</th>
            <th className="whitespace-nowrap pb-3 pl-6 text-right font-medium">Max</th>
            <th className="whitespace-nowrap pb-3 pl-6 text-right font-medium">
              Percentile
              <div className="text-[10px] normal-case text-muted-foreground/70">(current)</div>
            </th>
          </tr>
        </thead>
        <tbody>
          {panels.map((panel) => {
            const color = getEmaColor(panel.ema_period, theme);
            return (
              <tr key={panel.ema_period} className="border-t border-border">
                <td className="whitespace-nowrap py-3 pr-4">
                  <span className="inline-flex items-center gap-2 font-medium text-foreground">
                    <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: color }} />
                    EMA {panel.ema_period}
                  </span>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-center font-semibold text-foreground">
                  {panel.current_value}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-center text-muted-foreground">
                  {panel.median.toFixed(0)}
                </td>
                <td className="py-3 pl-4">
                  <DistributionCell panel={panel} color={color} theme={theme} />
                </td>
                <td className="whitespace-nowrap py-3 pl-6 text-right">
                  <div className="text-lg font-bold text-foreground">{panel.p95.toFixed(0)}</div>
                  <div className="text-[10px] uppercase tracking-wide text-gold">P95</div>
                </td>
                <td className="whitespace-nowrap py-3 pl-6 text-right">
                  <div className="text-lg font-bold text-foreground">{panel.max.toFixed(0)}</div>
                  <div className="text-[10px] uppercase tracking-wide text-gold">Max</div>
                </td>
                <td className="whitespace-nowrap py-3 pl-6 text-right font-semibold" style={{ color }}>
                  {panel.percentile.toFixed(0)}%
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <div className="mt-4 flex items-center gap-6 text-[11px] text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full border-2" style={{ borderColor: theme.text }} />
          Current
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-3 border-l border-dashed" style={{ borderColor: theme.text }} />
          Median
        </span>
      </div>
    </div>
  );
}

export default TimeAwaySummary;
