import { getChartTheme } from "@/lib/plotlyTheme";

// Sin decimales redondea cualquier % menor a 0.5 a "0%", lo cual es
// enganoso cuando SI hubo ocurrencias (count > 0). En ese caso se muestra
// con 1 decimal para que no desaparezca la evidencia de que ocurrio.
function formatPct(pct) {
  const rounded = Math.round(pct);
  if (pct > 0 && rounded === 0) return `${pct.toFixed(1)}%`;
  return `${rounded}%`;
}

function StrikeStreakTable({ panel }) {
  const theme = getChartTheme();
  const color = panel.type === "Green" ? theme.green : theme.red;

  return (
    <div
      className="rounded-lg border bg-card p-3"
      style={panel.is_current ? { borderColor: "var(--gold)", borderWidth: 2 } : { borderColor: "var(--border)" }}
    >
      <div className="mb-2 flex items-center gap-2 text-sm">
        <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: color }} />
        <span className="font-medium text-foreground">{panel.type} streaks</span>
        {panel.is_current && (
          <span className="ml-auto text-xs font-semibold text-gold">Current: {panel.current_length}</span>
        )}
      </div>

      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-muted-foreground">
            <th className="pb-1 font-medium">Length</th>
            <th className="pb-1 font-medium">Count</th>
            <th className="pb-1 font-medium">%</th>
          </tr>
        </thead>
        <tbody>
          {panel.rows.map((row) => {
            const isCurrentRow = panel.is_current && row.length === panel.current_length;
            return (
              <tr
                key={row.length}
                className="border-t border-border"
                style={isCurrentRow ? { background: "rgba(250, 204, 21, 0.12)" } : undefined}
              >
                <td className="py-1 font-medium text-foreground">
                  {row.length}
                  {isCurrentRow ? " ←" : ""}
                </td>
                <td className="py-1 text-foreground">{row.count}</td>
                <td className="py-1 font-semibold" style={{ color }}>
                  {formatPct(row.pct)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default StrikeStreakTable;
