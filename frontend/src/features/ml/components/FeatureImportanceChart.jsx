import Plot from "react-plotly.js";
import { getChartTheme } from "@/lib/plotlyTheme";

// El backend ya manda top_features ordenadas desc por importancia -- se
// invierten aqui porque Plotly dibuja barras horizontales de abajo a arriba.
function FeatureImportanceChart({ features }) {
  const theme = getChartTheme();
  const sorted = [...features].reverse();

  const trace = {
    x: sorted.map((f) => f.importance),
    y: sorted.map((f) => f.feature),
    type: "bar",
    orientation: "h",
    marker: { color: theme.gold },
    hoverinfo: "x",
  };

  return (
    <Plot
      data={[trace]}
      layout={{
        showlegend: false,
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: theme.text, size: 10 },
        xaxis: { color: theme.text, gridcolor: theme.grid, zerolinecolor: theme.grid },
        yaxis: { color: theme.axisText, automargin: true },
        margin: { t: 8, b: 24, l: 8, r: 8 },
        autosize: true,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: "380px" }}
      useResizeHandler
    />
  );
}

export default FeatureImportanceChart;
