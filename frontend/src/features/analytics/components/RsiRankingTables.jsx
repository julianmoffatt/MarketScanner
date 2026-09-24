import { getChartTheme } from "@/lib/plotlyTheme";

function RankingTable({ title, rows, color }) {
  return (
    <div className="flex-1 rounded-md border border-border bg-background/40 p-2">
      <div className="mb-1 text-xs font-medium text-foreground">{title}</div>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-muted-foreground">
            <th className="pb-1 font-medium">#</th>
            <th className="pb-1 font-medium">Date</th>
            <th className="pb-1 font-medium">RSI</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={row.date} className="border-t border-border">
              <td className="py-0.5 text-muted-foreground">{idx + 1}</td>
              <td className="py-0.5 text-foreground">{row.date}</td>
              <td className="py-0.5 font-semibold" style={{ color }}>
                {row.rsi_value.toFixed(1)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Top 10 de lecturas mas altas (sobrecompra) y mas bajas (sobreventa) del
// historico de ese timeframe -- ranking simple sobre panel.rows, sin
// necesidad de tocar el backend (ya trae date+rsi_value por fila).
function RsiRankingTables({ panel }) {
  const theme = getChartTheme();
  const sortedDesc = [...panel.rows].sort((a, b) => b.rsi_value - a.rsi_value);
  const top10High = sortedDesc.slice(0, 10);
  const top10Low = sortedDesc.slice(-10).reverse();

  return (
    <div className="mt-2 grid grid-cols-2 gap-2">
      <RankingTable title="Top 10 Highest RSI" rows={top10High} color={theme.red} />
      <RankingTable title="Top 10 Lowest RSI" rows={top10Low} color={theme.green} />
    </div>
  );
}

export default RsiRankingTables;
