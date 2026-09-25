import { getChartTheme } from "@/lib/plotlyTheme";

// Compara el accuracy real contra un DummyClassifier que siempre predice la
// clase mayoritaria -- si el modelo no le saca ventaja clara, el accuracy
// "real" no representa ningun edge, por muy bien que suene aislado.
function BaselineComparison({ modelAccuracy, baselineAccuracy }) {
  const theme = getChartTheme();
  const beats = modelAccuracy > baselineAccuracy;
  const color = beats ? theme.green : theme.red;

  return (
    <div className="grid grid-cols-2 gap-4 text-center">
      <div>
        <div className="text-xs text-muted-foreground">Modelo</div>
        <div className="text-lg font-bold" style={{ color }}>
          {(modelAccuracy * 100).toFixed(1)}%
        </div>
      </div>
      <div>
        <div className="text-xs text-muted-foreground">Baseline (clase mayoritaria)</div>
        <div className="text-lg font-bold text-muted-foreground">{(baselineAccuracy * 100).toFixed(1)}%</div>
      </div>
      <div className="col-span-2 text-xs" style={{ color }}>
        {beats
          ? `+${((modelAccuracy - baselineAccuracy) * 100).toFixed(1)} pts sobre el baseline`
          : "No supera al baseline trivial"}
      </div>
    </div>
  );
}

export default BaselineComparison;
