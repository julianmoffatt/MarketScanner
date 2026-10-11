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
// Weekly, Daily, Trend duration y Strikes.
export const MEAN_REVERSION_GROUPS = [
  {
    label: "Weekly",
    columns: [
      pct("weekly_time_away_ema10_percentile", "Time away EMA10 %"),
      days("weekly_time_away_ema10", "Days away EMA10"),
      pct("weekly_extension_ema10_percentile", "Extension EMA10 %"),
      pct("weekly_extension_ema20_percentile", "Extension EMA20 %"),
    ],
  },
  {
    label: "Daily",
    columns: [
      pct("daily_time_away_ema10_percentile", "Time away EMA10 %"),
      days("daily_time_away_ema10", "Days away EMA10"),
      pct("daily_time_away_ema20_percentile", "Time away EMA20 %"),
      days("daily_time_away_ema20", "Days away EMA20"),
      pct("daily_time_away_ema50_percentile", "Time away EMA50 %"),
      days("daily_time_away_ema50", "Days away EMA50"),
      pct("daily_extension_ema10_percentile", "Extension EMA10 %"),
      pct("daily_extension_ema20_percentile", "Extension EMA20 %"),
    ],
  },
  {
    label: "Trend duration (daily)",
    columns: [
      { key: "trend_ema10_side", label: "EMA10 side", kind: "number", format: side, isSide: true },
      days("trend_ema10_duration", "EMA10 days"),
      pct("trend_ema10_percentile", "EMA10 %"),
      { key: "trend_ema20_side", label: "EMA20 side", kind: "number", format: side, isSide: true },
      days("trend_ema20_duration", "EMA20 days"),
      pct("trend_ema20_percentile", "EMA20 %"),
    ],
  },
  {
    label: "Strikes",
    columns: [
      candleColor("daily_type", "Daily"),
      days("daily_strike", "Daily strike"),
      pct("daily_strike_percentile", "Daily %"),
      candleColor("weekly_type", "Weekly"),
      days("weekly_strike", "Weekly strike"),
      pct("weekly_strike_percentile", "Weekly %"),
      candleColor("monthly_type", "Monthly"),
      days("monthly_strike", "Monthly strike"),
      pct("monthly_strike_percentile", "Monthly %"),
    ],
  },
];

// Orden con el que se abre la tabla: percentil de "time away" semanal, de mayor a menor.
export const MEAN_REVERSION_DEFAULT_SORT = {
  key: "weekly_time_away_ema10_percentile",
  direction: "desc",
};
