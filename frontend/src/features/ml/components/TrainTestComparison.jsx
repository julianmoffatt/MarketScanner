import { getChartTheme } from "@/lib/plotlyTheme";

const ROWS = [
  { key: "accuracy", label: "Accuracy" },
  { key: "precision", label: "Precision" },
  { key: "recall", label: "Recall" },
  { key: "f1", label: "F1" },
];

// Mismo modelo, prediciendo sobre train y sobre test -- una brecha grande
// (train mucho mas alto que test) es la señal clasica de overfitting: el
// modelo memorizo el ruido de train en vez de aprender algo generalizable.
function TrainTestComparison({ trainMetrics, testMetrics }) {
  const theme = getChartTheme();

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-xs text-muted-foreground">
          <th className="pb-1 font-medium"></th>
          <th className="pb-1 font-medium text-right">Train</th>
          <th className="pb-1 font-medium text-right">Test</th>
          <th className="pb-1 font-medium text-right">Brecha</th>
        </tr>
      </thead>
      <tbody>
        {ROWS.map(({ key, label }) => {
          const train = trainMetrics[key];
          const test = testMetrics[key];
          const gap = train - test;
          return (
            <tr key={key} className="border-t border-border">
              <td className="py-1 text-muted-foreground">{label}</td>
              <td className="py-1 text-right text-foreground">{(train * 100).toFixed(1)}%</td>
              <td className="py-1 text-right text-foreground">{(test * 100).toFixed(1)}%</td>
              <td className="py-1 text-right font-semibold" style={{ color: gap > 0.15 ? theme.red : theme.text }}>
                {gap >= 0 ? "+" : ""}
                {(gap * 100).toFixed(1)}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export default TrainTestComparison;
