import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { useTicker } from "../hooks/useTicker";
import { getZScoreReturn } from "../api/analyticsApi";
import ScreenHeader from "../components/ScreenHeader";
import { getChartTheme } from "@/lib/plotlyTheme";

const DAYS = Array.from({ length: 31 }, (_, i) => i + 1);
const DAY_TICKS = [1, 5, 10, 15, 20, 25, 31];
const EXTREME_SIGMA = 2;
const SIGMA_BANDS = [EXTREME_SIGMA, -EXTREME_SIGMA];
const EXTREME_COLOR = "#ff1f1f";

// Media del z-score y numero de observaciones por dia del mes. El n se muestra
// en el hover porque los dias 29-31 tienen menos datos y sus medias son menos fiables.
function statsByDay(rows) {
  const sum = new Array(32).fill(0);
  const count = new Array(32).fill(0);
  for (const row of rows) {
    sum[row.day] += row.z_score;
    count[row.day] += 1;
  }
  return DAYS.map((day) => ({
    day,
    count: count[day],
    mean: count[day] ? sum[day] / count[day] : 0,
  }));
}

function ZScoreReturns() {
  const { ticker } = useTicker();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setData(null);
    getZScoreReturn(ticker)
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

  const rows = data?.rows ?? [];

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader
        title="Returns - ZScore"
        subtitle="How many standard deviations does the daily return move? · Distribution across the day of the month"
      />
      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {rows.length > 0 && <ZScoreCharts rows={rows} currentZScore={data.current_z_score} />}
    </div>
  );
}

function ZScoreCharts({ rows, currentZScore }) {
  const theme = getChartTheme();
  const today = rows[rows.length - 1].day;
  const stats = statsByDay(rows);

  const isExtreme = (r) => Math.abs(r.z_score) > EXTREME_SIGMA;
  const normalRows = rows.filter((r) => !isExtreme(r));
  const extremeRows = rows.filter(isExtreme);

  const values = rows.map((r) => r.z_score);
  const yMin = Math.min(...values, -SIGMA_BANDS[0]);
  const yMax = Math.max(...values, SIGMA_BANDS[0]);
  const yPad = (yMax - yMin) * 0.05 || 1;

  const axis = { color: theme.text, gridcolor: theme.grid, zerolinecolor: theme.grid };
  const dayAxis = { ...axis, range: [0.5, 31.5], tickvals: DAY_TICKS };

  const bandShapes = SIGMA_BANDS.map((sigma) => ({
    type: "line", xref: "paper", x0: 0, x1: 1, yref: "y", y0: sigma, y1: sigma,
    line: { color: theme.band, width: 1.5, dash: "dot" },
  }));
  const bandLabels = SIGMA_BANDS.map((sigma) => ({
    xref: "paper", x: 1, xanchor: "left", yref: "y", y: sigma, yshift: 9,
    text: `${sigma > 0 ? "+" : ""}${sigma}σ`, showarrow: false, font: { color: theme.band, size: 10 },
  }));

  const scatter = (
    <Plot
      data={[
        {
          x: normalRows.map((r) => r.day),
          y: normalRows.map((r) => r.z_score),
          type: "scatter",
          mode: "markers",
          marker: { color: theme.accentDark, size: 4, opacity: 0.35 },
          hovertemplate: "Day %{x} · z = %{y:.2f}<extra></extra>",
        },
        {
          x: extremeRows.map((r) => r.day),
          y: extremeRows.map((r) => r.z_score),
          type: "scatter",
          mode: "markers",
          marker: { color: EXTREME_COLOR, size: 6, opacity: 1 },
          hovertemplate: "Day %{x} · z = %{y:.2f}<extra></extra>",
        },
        {
          x: [today],
          y: [currentZScore],
          type: "scatter",
          mode: "markers",
          marker: { color: theme.highlight, size: 11, line: { color: theme.paper, width: 1.5 } },
          hovertemplate: "Latest · z = %{y:.2f}<extra></extra>",
        },
      ]}
      layout={{
        showlegend: false,
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: theme.text, size: 10 },
        xaxis: dayAxis,
        yaxis: { ...axis, range: [yMin - yPad, yMax + yPad], autorange: false },
        shapes: [
          ...bandShapes,
          {
            type: "rect", xref: "x", x0: today - 0.5, x1: today + 0.5, yref: "paper", y0: 0, y1: 1,
            fillcolor: theme.highlight, opacity: 0.1, line: { width: 0 }, layer: "below",
          },
        ],
        annotations: bandLabels,
        margin: { t: 16, b: 28, l: 40, r: 56 },
        autosize: true,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: "300px" }}
      useResizeHandler
    />
  );

  const bars = (
    <Plot
      data={[
        {
          x: stats.map((s) => s.day),
          y: stats.map((s) => s.mean),
          customdata: stats.map((s) => s.count),
          type: "bar",
          marker: { color: stats.map((s) => (s.mean >= 0 ? theme.green : theme.red)) },
          hovertemplate: "Day %{x} · mean z = %{y:.2f} (n=%{customdata})<extra></extra>",
        },
      ]}
      layout={{
        showlegend: false,
        bargap: 0.2,
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: theme.text, size: 10 },
        xaxis: dayAxis,
        yaxis: { ...axis, zeroline: true },
        margin: { t: 16, b: 28, l: 40, r: 56 },
        autosize: true,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: "200px" }}
      useResizeHandler
    />
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col rounded-lg border border-border bg-card p-2">
        <div className="px-2 text-xs text-muted-foreground">
          Daily return z-score by day of month · latest: {currentZScore.toFixed(2)}σ (highlighted) · red = beyond ±{EXTREME_SIGMA}σ ({extremeRows.length} of {rows.length})
        </div>
        {scatter}
      </div>
      <div className="flex flex-col rounded-lg border border-border bg-card p-2">
        <div className="px-2 text-xs text-muted-foreground">
          Mean z-score by day of month (hover for number of observations)
        </div>
        {bars}
      </div>
    </div>
  );
}

export default ZScoreReturns;
