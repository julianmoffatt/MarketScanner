// Un bin por cada valor entero exacto (sin agrupar/cap): si el rango va de
// 1 a 200, salen 200 barras. Los datos que consume esto (time_away,
// num_days) son siempre conteos enteros, asi que no hay perdida de
// precision por bins fraccionarios.
export function histogram(values) {
  const min = Math.min(...values);
  const max = Math.max(...values);

  const bins = [];
  for (let v = min; v <= max; v++) {
    bins.push({ x0: v, x1: v + 1, count: 0 });
  }

  values.forEach((value) => {
    bins[value - min].count += 1;
  });

  return bins;
}
