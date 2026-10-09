import Plot from "react-plotly.js";
import { getChartTheme } from "@/lib/plotlyTheme";

const DAYS = Array.from({ length: 31 }, (_, i) => i + 1);
const DAY_TICKS = [1, 5, 10, 15, 20, 25, 31];
const EXPECTED_TAIL_PERCENT = 5;
const EXCLUDED_TIMEFRAMES = ["weekly"];

// Las fechas llegan como "YYYY-MM-DD" (UTC), asi que el dia del mes son los
// dos ultimos caracteres.
const dayOfMonth = (date) => Number(date.slice(8, 10));

// Por cada dia del mes: cuantas observaciones hay y que % queda por debajo de
// p5 / por encima de p95. Es un % sobre las observaciones DE ESE DIA (los dias
// 29-31 tienen menos), asi que se pueden comparar entre dias; si no hubiera
// efecto del dia del mes, cada cola rondaria el 5%.
function tailsByDay(rows, p05, p95) {
  const total = new Array(32).fill(0);
  const low = new Array(32).fill(0);
  const high = new Array(32).fill(0);
  for (const row of rows) {
    const value = row.extension_to_mean;
    if (value === null || value === undefined) continue;
    const day = dayOfMonth(row.date);
    total[day] += 1;
    if (value < p05) low[day] += 1;
    else if (value > p95) high[day] += 1;
  }
  return DAYS.map((day) => ({
    day,
    total: total[day],
    low: total[day] ? (low[day] / total[day]) * 100 : 0,
    high: total[day] ? (high[day] / total[day]) * 100 : 0,
  }));
}

function DayPanel({ panel }) {
  const theme = getChartTheme();
  const rows = panel.rows.filter((r) => r.extension_to_mean !== null && r.extension_to_mean !== undefined);
  const today = dayOfMonth(rows[rows.length - 1].date);
  const tails = tailsByDay(rows, panel.p05, panel.p95);

  const values = rows.map((r) => r.extension_to_mean);
  const yMin = Math.min(...values, panel.p05);
  const yMax = Math.max(...values, panel.p95);
  const yPad = (yMax - yMin) * 0.05 || 1;

  const band = (value, label) => ({
    shape: {
      type: "line", xref: "paper", x0: 0, x1: 1, yref: "y", y0: value, y1: value,
      line: { color: theme.band, width: 1.5 },
    },
    annotation: {
      xref: "paper", x: 1, xanchor: "left", yref: "y", y: value, yshift: 9,
      text: `${label} (${value.toFixed(1)})`, showarrow: false, font: { color: theme.band, size: 10 },
    },
  });
  const upper = band(panel.p95, "p95");
  const lower = band(panel.p05, "p5");

  const axis = { color: theme.text, gridcolor: theme.grid, zerolinecolor: theme.grid };
  const dayAxis = { ...axis, range: [0.5, 31.5], tickvals: DAY_TICKS };

  const scatter = (
    <Plot
      data={[
        {
          x: rows.map((r) => dayOfMonth(r.date)),
          y: values,
          type: "scatter",
          mode: "markers",
          marker: { color: theme.accentDark, size: 4, opacity: 0.35 },
          hoverinfo: "x+y",
        },
        {
          x: [today],
          y: [panel.current_value],
          type: "scatter",
          mode: "markers",
          marker: { color: theme.highlight, size: 11, line: { color: theme.paper, width: 1.5 } },
          hoverinfo: "y",
        },
      ]}
      layout={{
        title: { text: `EMA${panel.ema_period} · ${panel.timeframe.toUpperCase()}`, font: { color: theme.axisText, size: 13 } },
        showlegend: false,
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: theme.text, size: 10 },
        xaxis: dayAxis,
        yaxis: { ...axis, range: [yMin - yPad, yMax + yPad], autorange: false },
        shapes: [
          upper.shape,
          lower.shape,
          {
            type: "rect", xref: "x", x0: today - 0.5, x1: today + 0.5, yref: "paper", y0: 0, y1: 1,
            fillcolor: theme.highlight, opacity: 0.1, line: { width: 0 }, layer: "below",
          },
        ],
        annotations: [upper.annotation, lower.annotation],
        margin: { t: 36, b: 28, l: 40, r: 72 },
        autosize: true,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: "240px" }}
      useResizeHandler
    />
  );

  const bars = (
    <Plot
      data={[
        {
          x: tails.map((t) => t.day),
          y: tails.map((t) => t.low),
          customdata: tails.map((t) => t.total),
          type: "bar",
          name: "Below p5",
          marker: { color: theme.green },
          hovertemplate: "Day %{x} · below p5: %{y:.1f}% (n=%{customdata})<extra></extra>",
        },
        {
          x: tails.map((t) => t.day),
          y: tails.map((t) => t.high),
          customdata: tails.map((t) => t.total),
          type: "bar",
          name: "Above p95",
          marker: { color: theme.red },
          hovertemplate: "Day %{x} · above p95: %{y:.1f}% (n=%{customdata})<extra></extra>",
        },
      ]}
      layout={{
        barmode: "group",
        bargap: 0.2,
        showlegend: true,
        legend: { orientation: "h", x: 0, y: 1.25, font: { size: 10 } },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: theme.text, size: 10 },
        xaxis: dayAxis,
        yaxis: { ...axis, ticksuffix: "%", rangemode: "tozero" },
        shapes: [
          {
            type: "line", xref: "paper", x0: 0, x1: 1, yref: "y", y0: EXPECTED_TAIL_PERCENT, y1: EXPECTED_TAIL_PERCENT,
            line: { color: theme.text, width: 1, dash: "dot" },
          },
        ],
        margin: { t: 28, b: 28, l: 40, r: 12 },
        autosize: true,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: "150px" }}
      useResizeHandler
    />
  );

  return (
    <div className="flex flex-col rounded-lg border border-border bg-card p-2">
      {scatter}
      <div className="mt-1 text-xs text-muted-foreground">
        % of observations beyond p5 / p95 by day of month (dotted line = {EXPECTED_TAIL_PERCENT}% expected with no day effect)
      </div>
      {bars}
    </div>
  );
}

function DayOfMonthPanels({ panels }) {
  const visible = panels.filter((p) => !EXCLUDED_TIMEFRAMES.includes(p.timeframe));
  const groups = Object.entries(Object.groupBy(visible, (p) => p.timeframe)).map(([timeframe, group]) => ({
    timeframe,
    panels: [...group].sort((a, b) => a.ema_period - b.ema_period),
  }));

  if (groups.length === 0) return null;

  return (
    <div className="flex flex-col gap-4">
      <div className="mt-2 text-xs font-semibold uppercase tracking-wide text-gold">
        By day of month · where do the extremes concentrate?
      </div>
      {groups.map(({ timeframe, panels: group }) => (
        <div
          key={timeframe}
          className="grid gap-4"
          style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}
        >
          {group.map((panel) => (
            <DayPanel key={`${panel.timeframe}-${panel.ema_period}`} panel={panel} />
          ))}
        </div>
      ))}
    </div>
  );
}

export default DayOfMonthPanels;
