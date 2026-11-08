// Columnas del screener de flips. A diferencia del de mean reversion, los grupos dependen de la
// respuesta del backend (que timeframes altos y cuantas casillas), asi que se construyen aqui
// a partir de ella.
//
// Cada timeframe alto es un grupo con: n (velas altas completas en el historico), la
// distribucion de flips en % (una casilla por numero de flips; la ultima es "ese numero o mas")
// y "LF p50", la mediana de en que vela baja ocurre el ultimo flip.

const whole = (v) => String(Math.round(v));
const oneDecimal = (v) => v.toFixed(1);

const TITLES = {
  weekly: "Weekly open",
  monthly: "Monthly open",
  quarterly: "Quarterly open",
  yearly: "Yearly open",
};

export function buildFlipGroups(buckets) {
  return Object.entries(buckets).map(([timeframe, labels]) => {
    const columns = [
      { key: `${timeframe}_n`, label: "n", kind: "number", format: whole, isCount: true },
      ...labels.map((label, bucket) => ({
        key: `${timeframe}_b${bucket}`,
        label,
        kind: "number",
        format: oneDecimal,
        bucket,
        currentKey: `${timeframe}_current`,
      })),
    ];
    // La semana solo tiene unas pocas velas diarias: la mediana del ultimo flip no aporta nada.
    if (timeframe !== "weekly") {
      columns.push({ key: `${timeframe}_lf`, label: "LF p50", kind: "number", format: oneDecimal });
    }
    return { label: TITLES[timeframe] ?? timeframe, columns };
  });
}

// El backend manda un bloque por timeframe alto; la tabla necesita una fila plana (campo -> valor).
export function flattenFlipRows(rows) {
  return rows.map((row) => {
    const flat = { ticker: row.ticker };
    for (const block of row.blocks) {
      const tf = block.timeframe;
      flat[`${tf}_n`] = block.occurrences;
      block.distribution.forEach((value, bucket) => {
        flat[`${tf}_b${bucket}`] = value;
      });
      flat[`${tf}_lf`] = block.last_flip_p50;
      flat[`${tf}_current`] = block.current_bucket;
    }
    return flat;
  });
}

export const FLIPS_DEFAULT_SORT = { key: "ticker", direction: "asc" };
