import { getChartTheme } from "@/lib/plotlyTheme";

function withAlpha(color, alpha) {
  if (color.startsWith("oklch(")) return color.replace(")", ` / ${alpha})`);
  return color;
}

// matrix[i][j] = muestras con clase real labels[i] predichas como labels[j].
// La diagonal (aciertos) se resalta en dorado; fuera de diagonal (errores)
// en gris tenue -- de un vistazo se ve si el modelo confunde una clase mas
// que otra, algo que precision/recall por separado no muestran tan directo.
function ConfusionMatrixTable({ confusion }) {
  const theme = getChartTheme();
  const { labels, matrix } = confusion;
  const total = matrix.flat().reduce((a, b) => a + b, 0);

  return (
    <table className="w-full table-fixed text-center text-sm">
      <thead>
        <tr>
          <th className="w-1/3"></th>
          <th className="pb-1 text-xs font-medium text-muted-foreground" colSpan={labels.length}>
            Predicted
          </th>
        </tr>
        <tr>
          <th className="text-xs font-medium text-muted-foreground">Actual</th>
          {labels.map((l) => (
            <th key={l} className="pb-1 text-xs font-medium text-muted-foreground">
              {l}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {matrix.map((row, i) => (
          <tr key={labels[i]}>
            <td className="pr-2 text-right text-xs font-medium text-muted-foreground">{labels[i]}</td>
            {row.map((count, j) => {
              const isDiagonal = i === j;
              return (
                <td key={j} className="p-1">
                  <div
                    className="rounded-md py-3 font-bold"
                    style={{
                      background: isDiagonal ? withAlpha(theme.gold, 0.18) : withAlpha(theme.text, 0.06),
                      color: isDiagonal ? theme.gold : theme.text,
                    }}
                  >
                    <div className="text-lg">{count}</div>
                    <div className="text-[10px] font-normal text-muted-foreground">
                      {total ? `${((count / total) * 100).toFixed(0)}%` : "—"}
                    </div>
                  </div>
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default ConfusionMatrixTable;
