import Plot from "react-plotly.js";
import { getChartTheme } from "@/lib/plotlyTheme";

// Reliability diagram: si el modelo estuviera perfectamente calibrado, sus
// puntos (prob. predicha media del bin vs. tasa real de acierto) caerian
// sobre la diagonal y=x. Cuanto mas se alejen, menos fiable es leer el
// numero de predict_proba como una probabilidad real.
function CalibrationChart({ calibration }) {
  const theme = getChartTheme();

  const diagonal = {
    x: [0, 1],
    y: [0, 1],
    type: "scatter",
    mode: "lines",
    line: { color: theme.grid, width: 1, dash: "dash" },
    hoverinfo: "skip",
    showlegend: false,
  };

  const model = {
    x: calibration.map((p) => p.prob_pred),
    y: calibration.map((p) => p.prob_true),
    type: "scatter",
    mode: "lines+markers",
    line: { color: theme.gold, width: 2 },
    marker: { color: theme.gold, size: 6 },
    hovertemplate: "predicho %{x:.2f} · real %{y:.2f}<extra></extra>",
    showlegend: false,
  };

  return (
    <Plot
      data={[diagonal, model]}
      layout={{
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: theme.text, size: 10 },
        xaxis: {
          title: { text: "Probabilidad predicha", font: { size: 10 } },
          range: [0, 1],
          color: theme.text,
          gridcolor: theme.grid,
          zerolinecolor: theme.grid,
        },
        yaxis: {
          title: { text: "Tasa real de acierto", font: { size: 10 } },
          range: [0, 1],
          color: theme.text,
          gridcolor: theme.grid,
          zerolinecolor: theme.grid,
        },
        margin: { t: 8, b: 40, l: 44, r: 12 },
        autosize: true,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: "220px" }}
      useResizeHandler
    />
  );
}

export default CalibrationChart;
