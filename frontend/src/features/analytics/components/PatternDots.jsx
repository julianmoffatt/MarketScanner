import { getChartTheme } from "@/lib/plotlyTheme";

// Representa un patron de 3 meses (ej. "GGR") como 3 puntos de color; si el
// patron esta incompleto (trimestre en curso), rellena los meses que aun no
// se conocen con un circulo punteado neutro.
function PatternDots({ pattern, size = "h-2.5 w-2.5" }) {
  const theme = getChartTheme();
  const letters = pattern.split("");
  while (letters.length < 3) letters.push(null);

  return (
    <div className="flex items-center gap-1">
      {letters.map((letter, i) => {
        if (letter === "G") {
          return <span key={i} className={`${size} shrink-0 rounded-full`} style={{ background: theme.green }} />;
        }
        if (letter === "R") {
          return <span key={i} className={`${size} shrink-0 rounded-full`} style={{ background: theme.red }} />;
        }
        return (
          <span
            key={i}
            className={`${size} shrink-0 rounded-full border border-dashed`}
            style={{ borderColor: "var(--muted-foreground)" }}
          />
        );
      })}
    </div>
  );
}

export default PatternDots;
