import { useEffect, useState } from "react";
import ScreenHeader from "@/features/analytics/components/ScreenHeader";
import { getMeanReversionScreener } from "../api/screenerApi";
import ScreenerTable from "../components/ScreenerTable";
import { MEAN_REVERSION_GROUPS, MEAN_REVERSION_DEFAULT_SORT } from "../config/meanReversionColumns";

// El backend no tiene (todavia) un endpoint que liste los universos de config.yaml,
// asi que de momento van aqui. El "value" es el nombre exacto de la clave en config.yaml.
const UNIVERSES = [
  { value: "mysymbols", label: "My symbols" },
  { value: "hyperliquid", label: "Hyperliquid" },
  { value: "crypto", label: "Crypto" },
  { value: "commodities", label: "Commodities" },
];

function Screener() {
  const [universe, setUniverse] = useState(UNIVERSES[0].value);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  // Pide los datos cada vez que cambia el universo. Mismo patron que el resto de pantallas:
  // "cancelled" evita guardar la respuesta de un universo viejo si el usuario ya cambio de
  // universo mientras esa peticion seguia en vuelo (llegarian en desorden).
  useEffect(() => {
    let cancelled = false;
    setError(null);
    setData(null); // mientras tanto se muestra "Loading..."
    getMeanReversionScreener(universe)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [universe]);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 px-6 py-3">
      <ScreenHeader
        title="SCREENER · MEAN REVERSION"
        subtitle="Click a column header to sort · percentiles are within each asset's own history · gold = top or bottom 10%"
      >
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

      {error && <p className="text-sm text-destructive">Error: {error}</p>}
      {!data && !error && <p className="text-sm text-muted-foreground">Loading... (the first load can take a few seconds)</p>}

      {data && (
        <ScreenerTable
          groups={MEAN_REVERSION_GROUPS}
          rows={data.rows}
          defaultSort={MEAN_REVERSION_DEFAULT_SORT}
        />
      )}
    </div>
  );
}

export default Screener;
