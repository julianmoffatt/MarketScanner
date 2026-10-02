import { getChartTheme } from "@/lib/plotlyTheme";

function ReturnCell({ value, theme, cellPad }) {
  if (value === null || value === undefined) return <td className={`${cellPad} text-muted-foreground`}>—</td>;
  const color = value >= 0 ? theme.green : theme.red;
  return (
    <td className={`${cellPad} font-semibold`} style={{ color }}>
      {value > 0 ? "+" : ""}
      {value.toFixed(1)}%
    </td>
  );
}

// compact: solo la usa la primera fila de la pantalla (ver DeviationEmaTrend)
// para que las dos tablas de 10 filas quepan enteras sin scroll -- texto y
// padding mas pequeños, mismo contenido (siguen siendo top 10, no se recorta
// informacion).
function RankingTable({ title, rows, titleColor, theme, compact }) {
  const cellPad = compact ? "py-px" : "py-0.5";
  return (
    <div className={`${compact ? "" : "flex-1"} rounded-md border border-border bg-background/40 p-2`}>
      <div className={`${compact ? "mb-0.5 text-[10px]" : "mb-1 text-xs"} font-medium`} style={{ color: titleColor }}>
        {title}
      </div>
      <table className={`w-full ${compact ? "text-[10px]" : "text-xs"}`}>
        <thead>
          <tr className="text-left text-muted-foreground">
            <th className="pb-1 font-medium">#</th>
            <th className="pb-1 font-medium">Date</th>
            <th className="pb-1 font-medium">Deviation</th>
            <th className="pb-1 font-medium">+1</th>
            <th className="pb-1 font-medium">+3</th>
            <th className="pb-1 font-medium">+5</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={row.date} className="border-t border-border">
              <td className={`${cellPad} text-muted-foreground`}>{idx + 1}</td>
              <td className={`${cellPad} text-foreground`}>{row.date}</td>
              <td className={`${cellPad} text-muted-foreground`}>{row.deviation.toFixed(1)}%</td>
              <ReturnCell value={row.forward_return_1} theme={theme} cellPad={cellPad} />
              <ReturnCell value={row.forward_return_3} theme={theme} cellPad={cellPad} />
              <ReturnCell value={row.forward_return_5} theme={theme} cellPad={cellPad} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Top 10 mejores/peores retornos a 1/3/5 velas despues de cada Absorption/
// Rejection historica -- "que paso despues de esto, las veces que mas/menos
// funciono", viendo la trayectoria completa (+1/+3/+5) no solo el final.
// El ranking ordena por +5 (el horizonte mas largo); cada celda de retorno
// se colorea por su propio signo, ya que el +1 de un evento puede ser
// negativo aunque su +5 sea el que lo mete en el top de "mejores".
// Los eventos muy recientes (sin 5 velas de futuro todavia) llegan con
// forward_return_5=null desde el backend y se excluyen del ranking.
function DeviationForwardReturnRankings({ panel, compact = false }) {
  const theme = getChartTheme();
  const withReturn = panel.rows.filter((r) => r.forward_return_5 !== null && r.forward_return_5 !== undefined);
  const sortedDesc = [...withReturn].sort((a, b) => b.forward_return_5 - a.forward_return_5);
  const top10Best = sortedDesc.slice(0, 10);
  const top10Worst = sortedDesc.slice(-10).reverse();

  if (withReturn.length === 0) return null;

  return (
    <div className={`flex h-full flex-col ${compact ? "gap-1" : "gap-2"}`}>
      <RankingTable title="Top 10 Best Return" rows={top10Best} titleColor={theme.green} theme={theme} compact={compact} />
      <RankingTable title="Top 10 Worst Return" rows={top10Worst} titleColor={theme.red} theme={theme} compact={compact} />
    </div>
  );
}

export default DeviationForwardReturnRankings;
