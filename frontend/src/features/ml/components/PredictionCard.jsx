import { getChartTheme } from "@/lib/plotlyTheme";

function PredictionCard({ panel }) {
  const theme = getChartTheme();
  const isGreen = panel.predicted_type === "Green";
  const color = isGreen ? theme.green : theme.red;
  const confidence = (isGreen ? panel.probability_green : panel.probability_red) * 100;

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-sm font-semibold uppercase tracking-wide text-foreground">
          {panel.model_name.replace(/_/g, " ")}
        </span>
        <span
          className="rounded-full px-3 py-1 text-xs font-bold uppercase"
          style={{ color, border: `1px solid ${color}` }}
        >
          {panel.predicted_type}
        </span>
      </div>

      <div className="text-center text-3xl font-bold" style={{ color }}>
        {confidence.toFixed(1)}%
      </div>
      <div className="text-center text-xs text-muted-foreground">confianza en su prediccion</div>

      <div className="mt-4 flex h-2 overflow-hidden rounded-full bg-muted">
        <div style={{ width: `${panel.probability_green * 100}%`, background: theme.green }} />
        <div style={{ width: `${panel.probability_red * 100}%`, background: theme.red }} />
      </div>
      <div className="mt-1 flex justify-between text-xs text-muted-foreground">
        <span>Green {(panel.probability_green * 100).toFixed(1)}%</span>
        <span>Red {(panel.probability_red * 100).toFixed(1)}%</span>
      </div>
    </div>
  );
}

export default PredictionCard;
