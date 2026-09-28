import Plot from "react-plotly.js";
import { getEmaColor } from "@/lib/plotlyTheme";
import { histogram } from "../lib/histogram";

function withAlpha(color, alpha) {
  // Los tokens de theme vienen como oklch(...); les metemos el alpha con la
  // sintaxis "oklch(... / alpha)" en vez de convertir a otro espacio de color.
  if (color.startsWith("oklch(")) {
    return color.replace(")", ` / ${alpha})`);
  }
  return color;
}

function TimeAwayHistogramCard({ panel, timeframe, theme }) {
  const color = getEmaColor(panel.ema_period, theme);
  const values = panel.rows.map((r) => r.time_away);
  const bins = histogram(values);
  const counts = bins.map((b) => b.count);
  const maxCount = Math.max(...counts);
  const minPositiveCount = Math.min(...counts.filter((c) => c > 0));

  // Rango del eje log fijado a mano en vez de autorange: con muchos bins y
  // muchos ceros (EMA50/200, con colas largas de duraciones raras), el
  // autorange de Plotly para ejes log calcula mal el rango (se sale a
  // valores absurdos tipo [-12, 235] en vez de exponentes de base 10) --
  // fijarlo explicitamente evita el bug.
  const logPad = 0.15;
  const yAxisRange = [Math.log10(minPositiveCount) - logPad, Math.log10(maxCount) + logPad];

  // Intervalo semiabierto [x0, x1) -- con <= en ambos extremos, un valor que
  // cae justo en el borde entre dos bins (ej. value=6 con bins [5,6) y
  // [6,7)) empataba con el bin anterior por el orden del array.
  let currentBinIdx = bins.findIndex((b) => panel.current_value >= b.x0 && panel.current_value < b.x1);
  if (currentBinIdx === -1) currentBinIdx = bins.length - 1;
  const currentX = (bins[currentBinIdx].x0 + bins[currentBinIdx].x1) / 2;

  const trace = {
    x: bins.map((b) => (b.x0 + b.x1) / 2),
    y: bins.map((b) => b.count),
    type: "bar",
    marker: { color: bins.map((_, i) => (i === currentBinIdx ? color : withAlpha(color, 0.35))) },
    hoverinfo: "y",
  };

  const shapes = [
    {
      type: "line",
      xref: "x",
      x0: currentX,
      x1: currentX,
      yref: "paper",
      y0: 0,
      y1: 1,
      line: { color: theme.highlight, width: 2, dash: "dot" },
    },
  ];

  const annotations = [
    {
      xref: "x",
      x: currentX,
      yref: "y",
      y: maxCount,
      yanchor: "bottom",
      yshift: 8,
      text: `${panel.current_value}`,
      showarrow: false,
      font: { color: theme.paper, size: 15 },
      bgcolor: theme.highlight,
      borderpad: 5,
    },
  ];

  return (
    <div className="flex h-full min-h-[320px] flex-col gap-3 rounded-lg border border-border bg-card p-3">
      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-2 font-medium text-foreground">
          <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: color }} />
          EMA {panel.ema_period} <span className="text-xs uppercase text-muted-foreground">· {timeframe}</span>
        </span>
        <span className="text-sm text-muted-foreground">
          Current: <span className="text-base font-bold text-foreground">{panel.current_value}</span>
        </span>
      </div>

      <Plot
        data={[trace]}
        layout={{
          shapes,
          annotations,
          showlegend: false,
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { color: theme.text, size: 10 },
          xaxis: { color: theme.text, gridcolor: theme.grid, zerolinecolor: theme.grid, fixedrange: true },
          // Log en vez de lineal: la distribucion de time_away esta muy
          // sesgada (muchas rachas cortas, pocas largas), asi que en lineal
          // las barras a partir de 1-3 dias quedaban casi invisibles junto
          // al bin dominante. En log, la cola larga usa el alto completo del
          // chart en vez de aplastarse contra el eje. Rango fijo (ver
          // yAxisRange arriba) en vez de autorange, que se rompe en paneles
          // con muchos bins/ceros.
          yaxis: { visible: false, fixedrange: true, type: "log", range: yAxisRange, autorange: false },
          margin: { t: 26, b: 24, l: 4, r: 4 },
          bargap: 0.15,
          autosize: true,
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler
      />

      <div className="grid grid-cols-3 gap-2 text-center text-xs">
        <div>
          <div className="text-muted-foreground">P25</div>
          <div className="font-semibold text-foreground">{panel.p25.toFixed(0)}</div>
        </div>
        <div>
          <div className="text-muted-foreground">Median</div>
          <div className="font-semibold text-foreground">{panel.median.toFixed(0)}</div>
        </div>
        <div>
          <div className="text-muted-foreground">P95</div>
          <div className="font-semibold text-foreground">{panel.p95.toFixed(0)}</div>
        </div>
      </div>

      <div>
        <div className="mb-1 flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Historical percentile</span>
          <span className="font-semibold" style={{ color }}>
            {panel.percentile.toFixed(0)}%
          </span>
        </div>
        <div className="h-1.5 rounded-full bg-muted">
          <div
            className="h-full rounded-full"
            style={{ width: `${Math.min(100, Math.max(0, panel.percentile))}%`, background: color }}
          />
        </div>
      </div>
    </div>
  );
}

export default TimeAwayHistogramCard;
