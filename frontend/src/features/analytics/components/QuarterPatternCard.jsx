import Plot from "react-plotly.js";
import { getChartTheme } from "@/lib/plotlyTheme";
import PatternDots from "./PatternDots";

function withAlpha(color, alpha) {
  if (color.startsWith("oklch(")) return color.replace(")", ` / ${alpha})`);
  return color;
}

// Dorado/gris solo tiene sentido cuando SI hay un trimestre en curso que
// elimina patrones (is_current) -- fuera de eso "is_possible" es true para
// los 8 sin distincion real, asi que se usa un color neutro para todos.
function barColor(row, isCurrent, theme) {
  if (!isCurrent) return theme.accent;
  return row.is_possible ? theme.gold : withAlpha(theme.text, 0.35);
}

function StatBox({ label, children }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1">{children}</div>
    </div>
  );
}

// Franja de barritas: mismo orden/colores que el chart principal pero en
// miniatura, con "Most common"/"Least common" en los extremos.
function MiniRanking({ rows, isCurrent, theme }) {
  const maxCount = Math.max(...rows.map((r) => r.count), 1);
  return (
    <div>
      <div className="flex h-10 items-end gap-1">
        {rows.map((row) => (
          <div
            key={row.pattern}
            className="flex-1 rounded-t"
            style={{
              height: `${Math.max((row.count / maxCount) * 100, 4)}%`,
              background: barColor(row, isCurrent, theme),
            }}
          />
        ))}
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-muted-foreground">
        <span>Most common</span>
        <span>Least common</span>
      </div>
    </div>
  );
}

function QuarterPatternCard({ panel }) {
  const theme = getChartTheme();
  const rows = panel.rows;

  const trace = {
    x: rows.map((r) => r.pattern),
    y: rows.map((r) => r.count),
    type: "bar",
    marker: { color: rows.map((r) => barColor(r, panel.is_current, theme)) },
    text: rows.map((r) => `${r.pct.toFixed(0)}%`),
    textposition: "outside",
    textfont: { color: theme.axisText, size: 11 },
    hoverinfo: "x+y",
  };

  const mostFrequent = rows[0];

  return (
    <div className="flex flex-col gap-4 rounded-lg border border-border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="font-semibold uppercase tracking-wide text-foreground">
          Combination Distribution · {panel.quarter}
        </span>
        {panel.is_current && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="uppercase tracking-wide">Current Quarter</span>
            <PatternDots pattern={panel.current_prefix} />
          </div>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
        <div className="flex flex-col">
          <div className="h-[240px]">
            <Plot
              data={[trace]}
              layout={{
                yaxis: { title: { text: "Frequency", font: { size: 10 } }, color: theme.text, gridcolor: theme.grid },
                xaxis: { showticklabels: false, color: theme.text, gridcolor: theme.grid },
                showlegend: false,
                paper_bgcolor: "transparent",
                plot_bgcolor: "transparent",
                font: { color: theme.text, size: 10 },
                margin: { t: 16, b: 8, l: 44, r: 12 },
                bargap: 0.25,
                autosize: true,
              }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: "100%", height: "100%" }}
              useResizeHandler
            />
          </div>
          <div className="flex gap-1 px-11">
            {rows.map((row) => (
              <div key={row.pattern} className="flex flex-1 flex-col items-center gap-1">
                <PatternDots pattern={row.pattern} />
                {row.is_possible && panel.is_current && (
                  <span className="text-[9px] font-semibold uppercase tracking-wide" style={{ color: theme.gold }}>
                    Possible
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-col justify-between gap-4">
          <div className="grid grid-cols-2 gap-4">
            <StatBox label="Current (partial)">
              {panel.is_current ? (
                <PatternDots pattern={panel.current_prefix} />
              ) : (
                <span className="text-sm text-muted-foreground">—</span>
              )}
            </StatBox>
            <StatBox label="Most frequent">
              <div className="flex items-center gap-2">
                <PatternDots pattern={mostFrequent.pattern} />
                <span className="text-sm font-semibold" style={{ color: theme.gold }}>
                  {mostFrequent.pct.toFixed(0)}%
                </span>
              </div>
            </StatBox>
            <StatBox label="Occurrences">
              <span className="text-lg font-semibold text-foreground">{panel.occurrences}</span>
              <span className="ml-1 text-xs text-muted-foreground">quarters</span>
            </StatBox>
            <StatBox label="Still possible">
              {panel.is_current ? (
                <span className="text-lg font-semibold text-foreground">
                  {panel.still_possible} <span className="text-xs text-muted-foreground">of 8</span>
                </span>
              ) : (
                <span className="text-sm text-muted-foreground">—</span>
              )}
            </StatBox>
          </div>

          <MiniRanking rows={rows} isCurrent={panel.is_current} theme={theme} />
        </div>
      </div>
    </div>
  );
}

export default QuarterPatternCard;
