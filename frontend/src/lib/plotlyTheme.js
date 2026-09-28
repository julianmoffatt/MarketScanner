// Lee los colores del theme (index.css) en vez de hardcodear hex --
// si cambia la paleta, los charts de Plotly se actualizan solos.
function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export function getChartTheme() {
  return {
    paper: cssVar("--card"),
    grid: cssVar("--border"),
    text: cssVar("--muted-foreground"),
    axisText: cssVar("--foreground"),
    accent: cssVar("--chart-blue"),
    accentDark: cssVar("--chart-blue-dark"),
    accentLight: cssVar("--chart-blue-light"),
    purpleLight: cssVar("--chart-purple-light"),
    highlight: cssVar("--chart-orange"),
    highlightDark: cssVar("--chart-orange-dark"),
    highlightLight: cssVar("--chart-orange-light"),
    band: cssVar("--gold"),
    green: cssVar("--chart-green"),
    greenLight: cssVar("--chart-green-light"),
    red: cssVar("--chart-red"),
    redLight: cssVar("--chart-red-light"),
    gold: cssVar("--gold"),
    emaGray: cssVar("--ema-gray"),
    emaPurple: cssVar("--ema-purple"),
  };
}

// Color fijo por EMA (usado en Time Away): 10=gold, 20=gris, 50=azul, 200=morado.
export function getEmaColor(emaPeriod, theme) {
  const map = { 10: theme.gold, 20: theme.emaGray, 50: theme.accent, 200: theme.emaPurple };
  return map[emaPeriod] ?? theme.accent;
}
