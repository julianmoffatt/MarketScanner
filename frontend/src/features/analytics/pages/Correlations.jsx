import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { useTicker } from "../hooks/useTicker";
import { getCorrelations } from "../api/analyticsApi";
import ScreenHeader from "../components/ScreenHeader";
import { getChartTheme } from "@/lib/plotlyTheme";

// Colores de las lineas de referencia en el grafico; el activo seleccionado usa el color resaltado.
const PEER_COLORS = [
  "#6ea8fe", "#9ec5fe", "#a78bfa", "#c4b5fd", "#5eead4", "#99f6e4",
  "#f9a8d4", "#fbbf24", "#d4d4d8", "#a3a3a3", "#7dd3fc",
];

// Fondo de la celda de correlacion: verde si es positiva, rojo si es negativa, mas intenso
// cuanto mayor es el valor (la correlacion va de -1 a 1).
function cellBackground(value) {
  if (value === null || value === undefined) return undefined;
  const strength = Math.min(Math.abs(value), 1) * 45;
  const color = value >= 0 ? "var(--chart-green)" : "var(--chart-red)";
  return `color-mix(in srgb, ${color} ${strength.toFixed(0)}%, transparent)`;
}

function formatValue(value) {
  return value === null || value === undefined ? "–" : value.toFixed(2);
}

function Correlations() {
  const { ticker } = useTicker();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setData(null);
    getCorrelations(ticker)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScreenHeader
        title="CORRELATIONS"
        subtitle="Correlation and up/down betas of daily returns vs. indices, commodities and bitcoin"
      />
      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {!data && !error && (
        <p className="text-sm text-muted-foreground">
          Loading… the first time can take a while if any of the reference assets still has to be downloaded.
        </p>
      )}
      {data && (
        <>
          <CorrelationTable data={data} ticker={ticker} />
          <EquityCurves curves={data.curves} />
          {data.missing.length > 0 && (
            <p className="text-xs text-muted-foreground">No data for: {data.missing.join(", ")}</p>
          )}
        </>
      )}
    </div>
  );
}

// Columnas de cada periodo, en este orden: correlacion, beta cuando la referencia sube, beta cuando baja.
const COLUMNS = [
  { key: "correlation", label: "Corr", title: "Correlation of daily returns" },
  { key: "beta_up", label: "β+", title: "Beta on days the reference asset is up" },
  { key: "beta_down", label: "β−", title: "Beta on days the reference asset is down" },
];

function CorrelationTable({ data, ticker }) {
  const asset = ticker.toUpperCase();

  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <div className="mb-3 text-xs text-muted-foreground">
        {asset} vs. reference assets · daily log returns on common dates
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="text-xs uppercase tracking-wide text-gold">
              <th rowSpan={2} className="px-2 py-1.5 text-left font-medium">
                Asset
              </th>
              {data.windows.map((w) => (
                <th key={w} colSpan={COLUMNS.length} className="border-l border-border px-2 py-1.5 text-center font-medium">
                  {w}
                </th>
              ))}
            </tr>
            <tr className="text-xs text-muted-foreground">
              {data.windows.flatMap((w) =>
                COLUMNS.map((column, index) => (
                  <th
                    key={`${w}-${column.key}`}
                    title={column.title}
                    className={`px-2 py-1 text-center font-medium ${index === 0 ? "border-l border-border" : ""}`}
                  >
                    {column.label}
                  </th>
                )),
              )}
            </tr>
          </thead>
          <tbody>
            {data.peers.map((peer, index) => {
              const newGroup = index > 0 && data.peers[index - 1].group !== peer.group;
              return (
                <tr key={peer.symbol} className={newGroup ? "border-t-2 border-border" : "border-t border-border"}>
                  <td className="px-2 py-1.5 font-semibold text-foreground">
                    {peer.symbol}
                    <span className="ml-2 text-xs font-normal text-muted-foreground">{peer.group}</span>
                  </td>
                  {data.windows.flatMap((w) => {
                    const stats = peer.windows[w];
                    return COLUMNS.map((column, columnIndex) => {
                      const value = stats?.[column.key];
                      const days =
                        column.key === "beta_up"
                          ? stats?.observations_up
                          : column.key === "beta_down"
                            ? stats?.observations_down
                            : stats?.observations;
                      return (
                        <td
                          key={`${w}-${column.key}`}
                          title={`${days ?? 0} days`}
                          className={`px-2 py-1.5 text-center tabular-nums text-foreground ${
                            columnIndex === 0 ? "border-l border-border" : ""
                          }`}
                          style={{ background: column.key === "correlation" ? cellBackground(value) : undefined }}
                        >
                          {formatValue(value)}
                        </td>
                      );
                    });
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        β+ / β−: slope of {asset}&apos;s returns on the reference asset&apos;s returns, using only the days that asset was up / down.
        "–" = not enough history or days (at least 8 per side) in that window. Short windows are noisy.
      </p>
    </div>
  );
}

function EquityCurves({ curves }) {
  const theme = getChartTheme();
  const peers = curves.filter((c) => !c.selected);
  const selected = curves.filter((c) => c.selected);

  // Primero las referencias y al final el activo seleccionado, para que quede por encima.
  const traces = [...peers, ...selected].map((curve) => {
    const isSelected = curve.selected;
    const peerIndex = peers.indexOf(curve);
    return {
      x: curve.dates,
      y: curve.values,
      name: curve.symbol,
      type: "scatter",
      mode: "lines",
      line: isSelected
        ? { color: theme.highlight, width: 3.5 }
        : { color: PEER_COLORS[peerIndex % PEER_COLORS.length], width: 1.3 },
      opacity: isSelected ? 1 : 0.8,
      hovertemplate: `${curve.symbol} %{y:.1f}%<extra></extra>`,
    };
  });

  return (
    <div className="rounded-lg border border-border bg-card p-2">
      <div className="px-2 text-xs text-muted-foreground">
        Cumulative return over the last year, all assets starting at 0 % (click a legend entry to hide it)
      </div>
      <Plot
        data={traces}
        layout={{
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { color: theme.text, size: 10 },
          xaxis: { color: theme.text, gridcolor: theme.grid },
          yaxis: { color: theme.text, gridcolor: theme.grid, zerolinecolor: theme.text, ticksuffix: "%" },
          legend: { orientation: "v", x: 1.01, y: 1, font: { color: theme.axisText, size: 11 } },
          hovermode: "x",
          margin: { t: 16, b: 36, l: 48, r: 90 },
          autosize: true,
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%", height: "420px" }}
        useResizeHandler
      />
    </div>
  );
}

export default Correlations;
