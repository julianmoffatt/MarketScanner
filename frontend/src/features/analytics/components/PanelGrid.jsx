import Plot from "react-plotly.js";
import { getChartTheme } from "@/lib/plotlyTheme";

// Agrupa por lo que identifique la fila (por defecto: timeframe, o type
// cuando el panel no trae ema_period). Object.groupBy preserva el orden de
// primera aparicion tanto para las filas como para los paneles dentro de
// cada fila, así que el orden en que el backend emite los paneles determina
// el orden visual sin necesidad de un sort adicional para ese eje.
// `groupBy` permite que cada pantalla decida su propio criterio cuando el
// default no encaja (ej. Deviation EMA Trend agrupando por type solo, para
// que cada fila mezcle timeframes y ema_periods como columnas).
function defaultGroupKey(panel) {
  return panel.type !== undefined && panel.ema_period === undefined ? panel.type : panel.timeframe;
}

function groupPanels(panels, groupBy) {
  const groups = Object.groupBy(panels, groupBy);
  return Object.entries(groups).map(([key, groupPanels]) => ({
    key,
    panels: [...groupPanels].sort((a, b) => (a.ema_period ?? 0) - (b.ema_period ?? 0)),
  }));
}

// Absorption/Rejection (Deviation EMA Trend) siguen la misma convencion de
// color que Green/Red (Deviation Candles): negativo/soporte en verde,
// positivo/resistencia en rojo.
function markerColor(panel, theme) {
  if (panel.type === "Green" || panel.type === "Absorption") return theme.green;
  if (panel.type === "Red" || panel.type === "Rejection") return theme.red;
  return theme.accent;
}

// 81 -> "81st", 12 -> "12th", 3 -> "3rd", etc.
function ordinal(n) {
  const rounded = Math.round(n);
  const mod100 = rounded % 100;
  if (mod100 >= 11 && mod100 <= 13) return `${rounded}th`;
  const suffix = { 1: "st", 2: "nd", 3: "rd" }[rounded % 10] ?? "th";
  return `${rounded}${suffix}`;
}

// Cuando el panel trae ema_period y type a la vez (ej. Absorption/Rejection
// por EMA), el titulo muestra ambos: "EMA10 · DAILY (Absorption)". Cuando no
// trae ninguno de los dos (ej. RSI, solo timeframe), el timeframe queda solo.
// El percentil (si el panel lo trae) se agrega siempre al final.
function panelTitle(panel, showPercentile = true) {
  const parts = [];
  if (panel.ema_period !== undefined) {
    parts.push(`EMA${panel.ema_period}`);
  } else if (panel.type !== undefined) {
    parts.push(panel.type);
  }
  parts.push(panel.timeframe.toUpperCase());

  let title = parts.join(" · ");
  if (panel.ema_period !== undefined && panel.type !== undefined) {
    title += ` (${panel.type})`;
  }
  if (showPercentile && panel.percentile !== undefined) {
    title += ` [Percentile: ${ordinal(panel.percentile)}]`;
  }
  return title;
}

function Panel({ panel, yField, currentField, p5Field, p95Field, valueSuffix = "", currentGuideline = false, currentColor, currentTextColor, dataColor, panelFooter, footerLayout = "column", showPercentile = true, compact = false }) {
  const theme = getChartTheme();
  const rows = panel.rows;
  const currentValue = currentField ? panel[currentField] : undefined;
  const hasCurrent = currentValue !== undefined && rows.length > 0;
  const color = dataColor ?? markerColor(panel, theme);
  // Color del punto actual y su linea guia -- naranja por defecto (RSI,
  // etc.), pero configurable por pantalla (Distance from Mean pide azul
  // oscuro, mas legible contra los puntos de dispersion en azul claro).
  const highlightColor = currentColor ?? theme.highlight;
  // La etiqueta de texto puede llevar un color distinto al de la linea/punto
  // (ej. texto blanco con linea/punto azul, para mas contraste).
  const labelColor = currentTextColor ?? highlightColor;

  const traces = [
    {
      x: rows.map((r) => r.date),
      y: rows.map((r) => r[yField]),
      type: "scatter",
      mode: "markers",
      marker: { color, size: 6 },
      hoverinfo: "x+y",
    },
  ];

  const shapes = [];
  const annotations = [];

  if (hasCurrent) {
    const lastDate = rows[rows.length - 1].date;

    if (currentGuideline) {
      // Linea punteada desde el primer dato hasta el punto actual, al nivel
      // del valor actual -- como la linea de "precio actual" de TradingView.
      // layer:"above" para que se vea por encima de los puntos azules.
      shapes.push({
        type: "line",
        xref: "x",
        x0: rows[0].date,
        x1: lastDate,
        yref: "y",
        y0: currentValue,
        y1: currentValue,
        line: { color: highlightColor, width: 2.5, dash: "4px,2px" },
        layer: "above",
      });
    }

    traces.push({
      x: [lastDate],
      y: [currentValue],
      type: "scatter",
      mode: "markers",
      marker: { color: highlightColor, size: 11, line: { color: theme.paper, width: 1.5 } },
      hoverinfo: "y",
      cliponaxis: false,
    });
    // Anotacion en vez de "text" del trace: con xshift controlamos el hueco
    // exacto en pixeles entre el punto y la etiqueta, pegada al punto.
    annotations.push({
      xref: "x",
      x: lastDate,
      xanchor: "left",
      xshift: 8,
      yref: "y",
      y: currentValue,
      yanchor: "middle",
      text: `${currentValue.toFixed(1)}${valueSuffix}`,
      showarrow: false,
      font: { color: labelColor, size: 11 },
    });
  }

  // Bandas p5/p95: linea horizontal punteada + etiqueta, ambas en rojo.
  // Genericas via prop -- si el panel no trae el campo, simplemente no se dibujan.
  // yshift separa la etiqueta de la linea (si no, el texto queda montado
  // encima de la linea y se hace ilegible).
  const addBand = (value, label) => {
    if (value === undefined) return;
    shapes.push({
      type: "line",
      xref: "paper",
      x0: 0,
      x1: 1,
      yref: "y",
      y0: value,
      y1: value,
      line: { color: theme.band, width: 1.5 },
    });
    annotations.push({
      xref: "paper",
      x: 1,
      xanchor: "left",
      yref: "y",
      y: value,
      yshift: 9,
      text: `${label} (${value.toFixed(1)})`,
      showarrow: false,
      font: { color: theme.band, size: 10 },
    });
  };
  addBand(p95Field ? panel[p95Field] : undefined, "p95");
  addBand(p5Field ? panel[p5Field] : undefined, "p5");

  // Rango fijo con poco margen (5%) en vez del autorange de Plotly, que deja
  // bastante aire de mas alrededor del extremo -- asi el grueso de los
  // puntos (lo que no es outlier) se ve mas grande/zoomeado.
  const yValues = rows.map((r) => r[yField]);
  if (p95Field && panel[p95Field] !== undefined) yValues.push(panel[p95Field]);
  if (p5Field && panel[p5Field] !== undefined) yValues.push(panel[p5Field]);
  const yMin = Math.min(...yValues);
  const yMax = Math.max(...yValues);
  const yPad = (yMax - yMin) * 0.05 || Math.abs(yMax) * 0.05 || 1;
  const yRange = [yMin - yPad, yMax + yPad];

  const chart = (
    <Plot
      data={traces}
      layout={{
        title: {
          text: panelTitle(panel, showPercentile),
          font: { color: theme.axisText, size: 13 },
        },
        showlegend: false,
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: theme.text, size: 10 },
        xaxis: { color: theme.text, gridcolor: theme.grid, zerolinecolor: theme.grid },
        yaxis: {
          color: theme.text,
          gridcolor: theme.grid,
          zerolinecolor: theme.grid,
          range: yRange,
          autorange: false,
        },
        shapes,
        annotations,
        margin: { t: 36, b: 28, l: 40, r: 72 },
        autosize: true,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: "100%" }}
      useResizeHandler
    />
  );

  // footerLayout="row": grafica a la izquierda, panelFooter a la derecha
  // (ej. Deviation Trend con sus rankings) en vez de apilado debajo (ej. RSI).
  // compact: solo la primera fila de un screen lo pide (ver PanelGrid) para
  // que quepa entera sin scroll -- el resto de filas se quedan en su tamaño
  // normal, asi que esto NO es un ajuste global de min-h.
  if (footerLayout === "row") {
    return (
      <div className={`flex h-full ${compact ? "min-h-[180px]" : "min-h-[260px]"} flex-row gap-2 rounded-lg border border-border bg-card p-2`}>
        <div className="h-full min-w-0 flex-[3]">{chart}</div>
        {panelFooter && <div className="h-full min-w-0 flex-[2]">{panelFooter(panel, compact)}</div>}
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-[220px] flex-col rounded-lg border border-border bg-card p-2">
      <div className="min-h-[180px] flex-1">{chart}</div>
      {panelFooter && panelFooter(panel)}
    </div>
  );
}

// current_value/p05/p95 son el contrato generico que usan todos los paneles
// tipo TimeframesEma_Percentiles_and_CurrentValue_Panel del backend -- se
// pueden pisar por prop si algun screen usara otros nombres.
// columnsPerRow: fuerza N columnas fijas por fila en vez de que cada fila
// se auto-ajuste a la cantidad de paneles que tenga (util cuando un solo
// timeframe agrupa muchos paneles -- ej. 4 EMAs de daily -- y se prefiere
// que se envuelvan en 2 filas en vez de estirarse en una sola).
function PanelGrid({
  panels,
  yField,
  currentField = "current_value",
  p5Field = "p05",
  p95Field = "p95",
  valueSuffix = "",
  columnsPerRow,
  groupBy = defaultGroupKey,
  currentGuideline = false,
  currentColor,
  currentTextColor,
  dataColor,
  panelFooter,
  footerLayout = "column",
  showPercentile = true,
  compactFirstRow = false,
}) {
  const rows = groupPanels(panels, groupBy);
  const gridStyle = columnsPerRow
    ? { gridTemplateColumns: `repeat(${columnsPerRow}, minmax(0, 1fr))` }
    : { gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" };

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      {rows.map(({ key, panels: rowPanels }, rowIndex) => {
        const isCompactRow = compactFirstRow && rowIndex === 0;
        // Fila compacta: sin flex-1 (no se estira a llenar el espacio
        // sobrante) y con un alto fijo -- Plotly (autosize + resize
        // handler) encoge el chart a ese alto en vez de crecer sin limite,
        // que es lo que antes inflaba tambien las tablas de al lado via
        // h-full en cadena.
        return (
        <div
          key={key}
          className={isCompactRow ? "grid gap-4" : "grid flex-1 gap-4"}
          style={isCompactRow ? { ...gridStyle, height: 500 } : gridStyle}
        >
          {rowPanels.map((panel) => (
            <Panel
              key={`${panel.timeframe}-${panel.ema_period ?? ""}-${panel.type ?? ""}`}
              panel={panel}
              yField={yField}
              currentField={currentField}
              p5Field={p5Field}
              p95Field={p95Field}
              valueSuffix={valueSuffix}
              currentGuideline={currentGuideline}
              currentColor={currentColor}
              currentTextColor={currentTextColor}
              dataColor={dataColor}
              panelFooter={panelFooter}
              footerLayout={footerLayout}
              compact={compactFirstRow && rowIndex === 0}
              showPercentile={showPercentile}
            />
          ))}
        </div>
        );
      })}
    </div>
  );
}

export default PanelGrid;
