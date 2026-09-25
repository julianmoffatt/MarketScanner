// Icono generico (anillo + punto dorado) reutilizado en todas las pantallas
// para mantener el estilo homogeneo, en vez de un icono distinto por pantalla.
import { useTicker } from "../hooks/useTicker";

function ScreenIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 40 40" fill="none" className="shrink-0">
      <circle cx="20" cy="20" r="16" stroke="var(--border)" strokeWidth="2" />
      <path d="M20 4a16 16 0 0 1 11.3 27.3" stroke="var(--gold)" strokeWidth="2" strokeLinecap="round" />
      <circle cx="20" cy="20" r="3" fill="var(--gold)" />
    </svg>
  );
}

function ScreenHeader({ title, subtitle, children }) {
  const { ticker } = useTicker();
  return (
    <>

    <div className="relative flex flex-wrap items-center justify-between gap-4 rounded-lg border border-border bg-card px-4 py-1">
      <div className="flex items-center gap-3">
        <ScreenIcon />
        <div>
          <div className="text-sm font-semibold tracking-wide text-foreground">{title}</div>
          {subtitle && <div className="text-xs text-muted-foreground">{subtitle}</div>}
        </div>
      </div>
      {children}
      <span className="absolute left-1/2 -translate-x-1/2 font-semibold text-foreground">
        {ticker.toUpperCase()}
      </span>
    </div>
    </>
  );
}

export default ScreenHeader;
