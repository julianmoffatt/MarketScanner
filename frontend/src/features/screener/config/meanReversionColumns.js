// Descripcion de las columnas del screener de mean reversion.
//
// La tabla NO tiene un <th> y un <td> escritos a mano por columna: se genera recorriendo
// esta lista (la misma idea que ROWS en MetricsTable). Para anadir, quitar o reordenar una
// columna basta con tocar este archivo.
//
// Cada columna tiene:
//   key     -> nombre exacto del campo que manda el backend (MeanReversionScreener_Row)
//   label   -> texto de la cabecera
//   kind    -> "number" (se ordena de mayor a menor primero) o "text" (de A a Z primero)
//   format  -> como se muestra el valor (opcional; sin format se muestra tal cual)
//   isPercentile -> true para resaltar los percentiles extremos

const percentile = (v) => String(Math.round(v));
const whole = (v) => String(Math.round(v));
// El backend manda el lado de la tendencia como 1 (por encima de la EMA) o -1 (por debajo).
const side = (v) => (v > 0 ? "Above" : "Below");

const pct = (key, label) => ({ key, label, kind: "number", format: percentile, isPercentile: true });
const days = (key, label) => ({ key, label, kind: "number", format: whole });
const candleColor = (key, label) => ({ key, label, kind: "text", isCandleColor: true });

// El orden de los grupos es el orden en el que aparecen en la tabla:
// Strikes (diario, semanal, mensual), Trend duration (EMA10, EMA20), Time away (primero daily, luego weekly).
export const MEAN_REVERSION_GROUPS = [
  {
    label: "Daily strikes",
    columns: [
      candleColor("daily_type", "Candle"),
      days("daily_strike", "Strike"),
    ],
  },
  {
    label: "Weekly strikes",
    columns: [
      candleColor("weekly_type", "Candle"),
      days("weekly_strike", "Strike"),
    ],
  },
  {
    label: "Monthly strikes",
    columns: [
      candleColor("monthly_type", "Candle"),
      days("monthly_strike", "Strike"),
    ],
  },
  {
    label: "EMA10 trend duration (daily)",
    columns: [
      { key: "trend_ema10_side", label: "Side", kind: "number", format: side, isSide: true },
      days("trend_ema10_duration", "Days"),
      pct("trend_ema10_percentile", "Percentile"),
    ],
  },
  {
    label: "EMA20 trend duration (daily)",
    columns: [
      { key: "trend_ema20_side", label: "Side", kind: "number", format: side, isSide: true },
      days("trend_ema20_duration", "Days"),
      pct("trend_ema20_percentile", "Percentile"),
    ],
  },
  {
    label: "Time & extension (daily)",
    columns: [
      days("daily_time_away_ema10", "Days"),
      pct("daily_extension_ema10_percentile", "EXT 10 %"),
    ],
  },
  {
    label: "Time & extension (weekly)",
    columns: [
      days("weekly_time_away_ema10", "Weeks"),
      pct("weekly_extension_ema10_percentile", "EXT 10 %"),
    ],
  },
];

// Orden con el que se abre la tabla: semanas lejos de la EMA10 (weekly), de mayor a menor.
export const MEAN_REVERSION_DEFAULT_SORT = {
  key: "weekly_time_away_ema10",
  direction: "desc",
};
