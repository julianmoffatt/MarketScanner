import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import ScreenHeader from "@/features/analytics/components/ScreenHeader";
import { getFlipsScreener, getMeanReversionScreener } from "../api/screenerApi";
import ScreenerTable from "../components/ScreenerTable";
import { MEAN_REVERSION_GROUPS, MEAN_REVERSION_DEFAULT_SORT } from "../config/meanReversionColumns";
import { buildFlipGroups, flattenFlipRows, FLIPS_DEFAULT_SORT } from "../config/flipsColumns";

// El backend no tiene (todavia) un endpoint que liste los universos de config.yaml,
// asi que de momento van aqui. El "value" es el nombre exacto de la clave en config.yaml.
const UNIVERSES = [
  { value: "mysymbols", label: "My symbols" },
  { value: "mag7", label: "Magnificent 7" },
  { value: "hyperliquid", label: "Hyperliquid" },
  { value: "crypto", label: "Crypto" },
  { value: "commodities", label: "Commodities" },
];

// Cada pestana del screener: como pide sus datos y como los convierte en la tabla.
// Para anadir otro screener basta con otra entrada aqui y su funcion en screenerApi.js.
const VIEWS = {
  "mean-reversion": {
    label: "Mean reversion",
    title: "SCREENER · MEAN REVERSION",
    subtitle: "Click a column header to sort · percentiles are within each asset's own history · gold = top or bottom 10%",
    load: (universe) => getMeanReversionScreener(universe),
    toTable: (data) => ({ groups: MEAN_REVERSION_GROUPS, rows: data.rows, defaultSort: MEAN_REVERSION_DEFAULT_SORT }),
  },
  "flips-d": {
    label: "Flips (D)",
    title: "SCREENER · FLIPS · DAILY CANDLES",
    subtitle:
      "How often the direction of each weekly / monthly / quarterly / yearly candle is contested, measured with daily closes around its open · gold = flips of the current candle · LF p50 = median daily candle of the last flip",
    load: (universe) => getFlipsScreener(universe, "daily"),
    toTable: (data) => ({ groups: buildFlipGroups(data.buckets), rows: flattenFlipRows(data.rows), defaultSort: FLIPS_DEFAULT_SORT }),
  },
  "flips-m": {
    label: "Flips (M)",
    title: "SCREENER · FLIPS · MONTHLY CANDLES",
    subtitle:
      "How often the direction of each quarterly / yearly candle is contested, measured with monthly closes around its open · gold = flips of the current candle · LF p50 = median monthly candle of the last flip",
    load: (universe) => getFlipsScreener(universe, "monthly"),
    toTable: (data) => ({ groups: buildFlipGroups(data.buckets), rows: flattenFlipRows(data.rows), defaultSort: FLIPS_DEFAULT_SORT }),
  },
};

const DEFAULT_VIEW = "mean-reversion";

function Screener() {
  // La pestana vive en la URL (?view=flips-d): se puede enlazar y el boton "atras" funciona.
  const [searchParams, setSearchParams] = useSearchParams();
  const requested = searchParams.get("view");
  const viewKey = requested in VIEWS ? requested : DEFAULT_VIEW;
  const view = VIEWS[viewKey];

  const [universe, setUniverse] = useState(UNIVERSES[0].value);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  // Pide los datos cada vez que cambia el universo o la pestana. Mismo patron que el resto de
  // pantallas: "cancelled" evita guardar la respuesta de una peticion vieja si el usuario ya
  // cambio de universo o de pestana mientras seguia en vuelo (llegarian en desorden).
  useEffect(() => {
    let cancelled = false;
    setError(null);
    setData(null); // mientras tanto se muestra "Loading..."
    VIEWS[viewKey]
      .load(universe)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [universe, viewKey]);

  const table = data ? view.toTable(data) : null;

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 px-6 py-3">
      <ScreenHeader title={view.title} subtitle={view.subtitle}>
        <select
          value={universe}
          onChange={(e) => setUniverse(e.target.value)}
          className="rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground outline-none focus:border-gold"
        >
          {UNIVERSES.map((u) => (
            <option key={u.value} value={u.value}>
              {u.label}
            </option>
          ))}
        </select>
      </ScreenHeader>

      <nav className="flex gap-6 border-b border-border">
        {Object.entries(VIEWS).map(([key, { label }]) => (
          <button
            key={key}
            type="button"
            onClick={() => setSearchParams({ view: key })}
            aria-current={key === viewKey ? "page" : undefined}
            className={`border-b-2 pb-2 text-sm font-medium transition-colors ${
              key === viewKey
                ? "border-gold text-gold"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {label}
          </button>
        ))}
      </nav>

      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {!data && !error && <p className="text-sm text-muted-foreground">Loading... (the first load can take a few seconds)</p>}

      {table && (
        // key: al cambiar de pestana la tabla se crea de nuevo, asi su orden vuelve al de esa pestana.
        <ScreenerTable key={viewKey} groups={table.groups} rows={table.rows} defaultSort={table.defaultSort} />
      )}
      {data?.missing?.length > 0 && (
        <p className="text-xs text-muted-foreground">Not enough data for: {data.missing.join(", ")}</p>
      )}
    </div>
  );
}

export default Screener;
