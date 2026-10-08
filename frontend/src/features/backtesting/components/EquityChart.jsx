import Plot from "react-plotly.js";
import { getChartTheme } from "@/lib/plotlyTheme";

function EquityChart({ equity, benchmark }) {
  const theme = getChartTheme();

  const trace = (points, name, color) => ({
    x: points.map((p) => p.date),
    y: points.map((p) => p.value),
    type: "scatter",
    mode: "lines",
    name,
    line: { color, width: 2 },
    hovertemplate: `${name}: %{y:,.2f}<extra></extra>`,
  });

  return (
    <Plot
      data={[trace(equity, "Strategy", theme.gold), trace(benchmark, "Buy & Hold", theme.accent)]}
      layout={{
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: theme.text, size: 11 },
        xaxis: { color: theme.text, gridcolor: theme.grid },
        yaxis: { color: theme.text, gridcolor: theme.grid, tickformat: ",.0f" },
        legend: { orientation: "h", x: 0, y: 1.12 },
        hovermode: "x unified",
        margin: { t: 28, b: 40, l: 56, r: 12 },
        autosize: true,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: "380px" }}
      useResizeHandler
    />
  );
}

export default EquityChart;
