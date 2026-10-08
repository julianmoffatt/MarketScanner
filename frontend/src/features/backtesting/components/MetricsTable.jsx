const percent = (v) => `${(v * 100).toFixed(2)}%`;
const decimal = (v) => v.toFixed(2);
const integer = (v) => String(v);

const ROWS = [
  { key: "total_return", label: "Total return", format: percent },
  { key: "cagr", label: "CAGR", format: percent },
  { key: "volatility", label: "Volatility (annualized)", format: percent },
  { key: "sharpe", label: "Sharpe", format: decimal },
  { key: "sortino", label: "Sortino", format: decimal },
  { key: "max_drawdown", label: "Max drawdown", format: percent },
  { key: "max_drawdown_duration", label: "Max drawdown duration (bars)", format: integer },
  { key: "average_exposure", label: "Average exposure", format: percent },
  { key: "exposure_changes", label: "Exposure changes", format: integer },
];

function cell(metrics, row) {
  const value = metrics?.[row.key];
  return value === null || value === undefined ? "—" : row.format(value);
}

function MetricsTable({ metrics, benchmarkMetrics }) {
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-left uppercase tracking-wide text-gold">
          <th className="py-1.5 font-medium">Metric</th>
          <th className="py-1.5 text-right font-medium">Strategy</th>
          <th className="py-1.5 text-right font-medium">Buy & Hold</th>
        </tr>
      </thead>
      <tbody>
        {ROWS.map((row) => (
          <tr key={row.key} className="border-t border-border">
            <td className="py-1.5 text-muted-foreground">{row.label}</td>
            <td className="py-1.5 text-right font-semibold text-foreground">{cell(metrics, row)}</td>
            <td className="py-1.5 text-right font-semibold text-foreground">{cell(benchmarkMetrics, row)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default MetricsTable;
