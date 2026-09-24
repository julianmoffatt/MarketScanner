// Barra de progreso: rellena de 0 hasta el valor actual (sobre una escala
// 0..p95), con marcas verticales para P25/Median/P75/P95 debajo. Es la
// "regla" que le da contexto al numero de "Current" -- donde cae dentro del
// rango historico.
function TrendDurationSlider({ current, p25, median, p75, p95, color }) {
  const hasCurrent = current !== null && current !== undefined;
  const trackMax = Math.max(p95, hasCurrent ? current : 0, 1);
  const pct = (value) => Math.min(100, Math.max(0, (value / trackMax) * 100));

  const ticks = [
    { label: "P25", value: p25 },
    { label: "Median", value: median },
    { label: "P75", value: p75 },
    { label: "P95", value: p95 },
  ];

  return (
    <div className="mt-2">
      <div className="relative h-2 rounded-full bg-muted">
        {hasCurrent && (
          <>
            <div
              className="absolute inset-y-0 left-0 rounded-full"
              style={{ width: `${pct(current)}%`, background: color }}
            />
            <div
              className="absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2"
              style={{ left: `${pct(current)}%`, background: color, borderColor: "var(--card)" }}
            />
          </>
        )}
      </div>
      <div className="relative mt-1 h-8">
        {ticks.map((tick) => (
          <div
            key={tick.label}
            className="absolute top-0 -translate-x-1/2 text-center"
            style={{ left: `${pct(tick.value)}%` }}
          >
            <div className="mx-auto h-1.5 w-px bg-border" />
            <div className="mt-0.5 whitespace-nowrap text-[10px] text-muted-foreground">{tick.label}</div>
            <div className="whitespace-nowrap text-xs font-semibold text-foreground">
              {Number.isInteger(tick.value) ? tick.value : tick.value.toFixed(1)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TrendDurationSlider;
