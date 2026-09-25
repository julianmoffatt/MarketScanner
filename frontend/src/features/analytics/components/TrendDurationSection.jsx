import Plot from "react-plotly.js";
import { getChartTheme } from "@/lib/plotlyTheme";
import { histogram } from "../lib/histogram";
import TrendDurationSlider from "./TrendDurationSlider";

function withAlpha(color, alpha) {
  if (color.startsWith("oklch(")) return color.replace(")", ` / ${alpha})`);
  return color;
}

function ArrowIcon({ up }) {
  const theme = getChartTheme();
  const color = up ? theme.green : theme.red;
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      {up ? (
        <path d="M10 16V4M10 4L4 10M10 4l6 6" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      ) : (
        <path d="M10 4v12M10 16l-6-6M10 16l6-6" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      )}
    </svg>
  );
}

function TrendDurationSection({ panel }) {
  const theme = getChartTheme();
  const isAbove = panel.type === "Above";
  const color = isAbove ? theme.green : theme.red;

  const values = panel.rows.map((r) => r.num_days);
  const bins = histogram(values);
  const maxCount = Math.max(...bins.map((b) => b.count));

  // El resaltado "Now" solo tiene sentido en el lado que esta realmente en
  // curso -- el otro lado no tiene ninguna racha abierta, asi que ni se
  // marca una barra ni se dibuja la linea/anotacion "Now".
  // Intervalo semiabierto [x0, x1): con <= en ambos extremos, un valor que
  // cae justo en el borde entre dos bins empataba con el bin anterior.
  let currentBinIdx = panel.is_current
    ? bins.findIndex((b) => panel.current_value >= b.x0 && panel.current_value < b.x1)
    : -1;
  if (panel.is_current && currentBinIdx === -1) currentBinIdx = bins.length - 1;

  const trace = {
    x: bins.map((b) => (b.x0 + b.x1) / 2),
    y: bins.map((b) => b.count),
    type: "bar",
    marker: { color: bins.map((_, i) => (i === currentBinIdx ? color : withAlpha(color, 0.4))) },
    hoverinfo: "y",
  };

  const shapes = [];
  const annotations = [];
  if (panel.is_current) {
    const currentX = (bins[currentBinIdx].x0 + bins[currentBinIdx].x1) / 2;
    shapes.push({
      type: "line",
      xref: "x",
      x0: currentX,
      x1: currentX,
      yref: "paper",
      y0: 0,
      y1: 1,
      line: { color: theme.highlight, width: 1.5, dash: "dot" },
    });
    annotations.push({
      xref: "x",
      x: currentX,
      yref: "y",
      y: maxCount,
      yanchor: "bottom",
      yshift: 6,
      text: `Now<br>${panel.current_value}`,
      showarrow: false,
      font: { color: theme.highlight, size: 11 },
    });
  }

  return (
    <div className="flex flex-col gap-4 rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ArrowIcon up={isAbove} />
          <span className="font-semibold uppercase tracking-wide text-foreground">{panel.type} EMA 10 </span>
        </div>
        <span className="text-sm text-muted-foreground">
          Current <span className="font-semibold text-foreground">{panel.current_value}</span>
        </span>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
        <div className="h-[260px]">
          <Plot
            data={[trace]}
            layout={{
              yaxis: { title: { text: "Frequency", font: { size: 10 } }, color: theme.text, gridcolor: theme.grid },
              xaxis: { color: theme.text, gridcolor: theme.grid, zerolinecolor: theme.grid },
              shapes,
              annotations,
              showlegend: false,
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              font: { color: theme.text, size: 10 },
              margin: { t: 30, b: 28, l: 44, r: 12 },
              bargap: 0.15,
              autosize: true,
            }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: "100%", height: "100%" }}
            useResizeHandler
          />
        </div>

        <div className="flex flex-col justify-center gap-4">
          <div className="grid grid-cols-4 gap-2 text-center">
            <div>
              <div className="text-xs text-muted-foreground">Current</div>
              <div className="text-lg font-semibold text-foreground">{panel.current_value}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Median</div>
              <div className="text-lg font-semibold text-foreground">{Math.round(panel.median)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">P95</div>
              <div className="text-lg font-semibold text-foreground">{Math.round(panel.p95)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Percentile</div>
              <div
                className="text-lg font-semibold"
                style={{ color: panel.is_current ? theme.highlight : "var(--foreground)" }}
              >
                {panel.is_current ? `${Math.round(panel.percentile)}%` : "—"}
              </div>
            </div>
          </div>

          <TrendDurationSlider
            current={panel.is_current ? panel.current_value : null}
            p25={panel.p25}
            median={panel.median}
            p75={panel.p75}
            p95={panel.p95}
            color={color}
          />
        </div>
      </div>
    </div>
  );
}

export default TrendDurationSection;
