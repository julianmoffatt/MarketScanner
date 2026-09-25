import Plot from "react-plotly.js";
import { getChartTheme } from "@/lib/plotlyTheme";

// AUC=0.5 (la diagonal) es un modelo que no discrimina nada, equivalente a
// tirar una moneda. Cuanto mas se separe la curva real hacia la esquina
// superior izquierda, mejor separa las dos clases.
function RocChart({ roc }) {
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

  const curve = {
    x: roc.points.map((p) => p.fpr),
    y: roc.points.map((p) => p.tpr),
    type: "scatter",
    mode: "lines",
    line: { color: theme.gold, width: 2 },
    fill: "tozeroy",
    fillcolor: theme.gold.startsWith("oklch(") ? theme.gold.replace(")", " / 0.12)") : theme.gold,
    hovertemplate: "FPR %{x:.2f} · TPR %{y:.2f}<extra></extra>",
    showlegend: false,
  };

  return (
    <div>
      <div className="mb-1 text-right text-sm font-semibold" style={{ color: theme.gold }}>
        AUC {roc.auc.toFixed(3)}
      </div>
      <Plot
        data={[diagonal, curve]}
        layout={{
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { color: theme.text, size: 10 },
          xaxis: {
            title: { text: "False Positive Rate", font: { size: 10 } },
            range: [0, 1],
            color: theme.text,
            gridcolor: theme.grid,
            zerolinecolor: theme.grid,
          },
          yaxis: {
            title: { text: "True Positive Rate", font: { size: 10 } },
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
    </div>
  );
}

export default RocChart;
