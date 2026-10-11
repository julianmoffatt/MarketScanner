import { useMemo, useState } from "react";

// ---------------------------------------------------------------------------
// ORDENAR
// ---------------------------------------------------------------------------

// Compara dos valores de una columna.
//  - Los valores vacios (null) van SIEMPRE al final, ordenes de mayor a menor o al reves.
//    Si usaramos una resta, un null se comportaria como 0 y mezclaria las filas sin datos.
//  - Numeros se comparan restando; textos ("Green"/"Red", el ticker) con localeCompare.
//  - "direction" solo invierte el resultado, nunca la posicion de los vacios.
function compareValues(a, b, direction) {
  const aEmpty = a === null || a === undefined;
  const bEmpty = b === null || b === undefined;
  if (aEmpty && bEmpty) return 0;
  if (aEmpty) return 1;
  if (bEmpty) return -1;

  const result = typeof a === "string" ? a.localeCompare(b) : a - b;
  return direction === "asc" ? result : -result;
}

// ---------------------------------------------------------------------------
// MOSTRAR UNA CELDA
// ---------------------------------------------------------------------------

// Un percentil por debajo de 10 o por encima de 90 esta en una cola de su historia:
// se resalta en dorado para que se vea de un vistazo sin leer todos los numeros.
// El 0 exacto NO se resalta: los "time away" valen 0 cuando la vela esta dentro de la banda
// (no hay racha), y ningun otro percentil puede ser exactamente 0.
function percentileClass(value) {
  if (value === null || value === undefined) return "text-foreground";
  const isExtreme = value >= 90 || (value > 0 && value <= 10);
  return isExtreme ? "font-semibold text-gold" : "text-foreground";
}

function cellClass(column, value) {
  if (column.isPercentile) return percentileClass(value);
  if (column.isCandleColor) return value === "Green" ? "text-chart-green" : "text-chart-red";
  if (column.isSide) return value > 0 ? "text-chart-green" : "text-chart-red";
  return "text-foreground";
}

function cellText(column, value) {
  // "—" para los datos que no existen (por ejemplo, poca historia mensual en un valor reciente).
  if (value === null || value === undefined) return "—";
  return column.format ? column.format(value) : String(value);
}

// ---------------------------------------------------------------------------
// CABECERAS PULSABLES
// ---------------------------------------------------------------------------

const TICKER_COLUMN = { key: "ticker", label: "Ticker", kind: "text" };

// Flecha de la columna por la que esta ordenada la tabla.
function SortArrow({ active, direction }) {
  // Si no esta activa se pinta invisible, pero ocupa su hueco para que el ancho no "salte".
  if (!active) return <span className="opacity-0">▲</span>;
  return <span>{direction === "asc" ? "▲" : "▼"}</span>;
}

// Boton de una cabecera. Es un <button> (no un <th> con onClick) para que tambien se pueda
// usar con el teclado. Esta definido FUERA de ScreenerTable a proposito: un componente
// definido dentro de otro se crea de nuevo en cada pintado y React lo desmonta y monta cada vez.
function SortButton({ column, sort, onSort }) {
  const active = sort.key === column.key;
  return (
    <button
      type="button"
      onClick={() => onSort(column)}
      className={`flex w-full items-center gap-1 whitespace-nowrap uppercase tracking-wide transition-colors hover:text-foreground ${
        column.kind === "text" ? "justify-start" : "justify-end"
      } ${active ? "text-foreground" : "text-gold"}`}
    >
      {column.label}
      <SortArrow active={active} direction={sort.direction} />
    </button>
  );
}

// "aria-sort" le dice a los lectores de pantalla (y a los tests) como esta ordenada cada columna.
function ariaSort(sort, column) {
  if (sort.key !== column.key) return "none";
  return sort.direction === "asc" ? "ascending" : "descending";
}

// ---------------------------------------------------------------------------
// COMPONENTE
// ---------------------------------------------------------------------------

function ScreenerTable({ groups, rows, defaultSort }) {
  // Que columna esta activa y en que sentido. Es estado de React: al cambiarlo, el
  // componente se vuelve a pintar con las filas reordenadas.
  const [sort, setSort] = useState(defaultSort);

  // Filas ya ordenadas. useMemo evita repetir el orden en cada pintado si no han cambiado
  // ni las filas ni el criterio.
  const sortedRows = useMemo(
    () =>
      // [...rows] hace una COPIA: sort() modifica el array original, y en React nunca se
      // debe modificar directamente lo que viene de las props o del estado.
      [...rows].sort(
        (a, b) =>
          compareValues(a[sort.key], b[sort.key], sort.direction) ||
          a.ticker.localeCompare(b.ticker), // empate: orden alfabetico por ticker, siempre estable
      ),
    [rows, sort],
  );

  // Click en una cabecera:
  //  - misma columna que ya estaba activa -> invierte el sentido (mayor<->menor)
  //  - otra columna -> pasa a ser la activa, empezando por lo mas util: los numeros de
  //    mayor a menor (los percentiles mas altos arriba) y los textos de A a Z.
  function handleSort(column) {
    setSort((current) => {
      if (current.key === column.key) {
        return { key: column.key, direction: current.direction === "desc" ? "asc" : "desc" };
      }
      return { key: column.key, direction: column.kind === "text" ? "asc" : "desc" };
    });
  }

  return (
    // overflow-auto: la tabla tiene ~30 columnas y no cabe en pantalla, asi que este
    // contenedor desplaza en horizontal y en vertical SIN mover el resto de la pagina.
    <div className="min-h-0 flex-1 overflow-auto rounded-lg border border-border bg-card">
      <table className="w-full border-separate border-spacing-0 text-xs">
        {/* sticky top-0: las cabeceras se quedan arriba al desplazar hacia abajo. */}
        <thead className="sticky top-0 z-10 bg-card">
          {/* Fila 1: nombre de cada grupo. colSpan hace que abarque todas sus columnas;
              rowSpan={2} en el ticker hace que ocupe las dos filas de cabecera. */}
          <tr>
            <th
              rowSpan={2}
              aria-sort={ariaSort(sort, TICKER_COLUMN)}
              className="sticky left-0 z-20 bg-card px-2 py-1 align-bottom font-medium"
            >
              <SortButton column={TICKER_COLUMN} sort={sort} onSort={handleSort} />
            </th>
            {groups.map((group) => (
              <th
                key={group.label}
                colSpan={group.columns.length}
                className="border-l border-border px-2 py-1.5 text-center text-xs font-semibold uppercase tracking-wide text-foreground"
              >
                {group.label}
              </th>
            ))}
          </tr>
          {/* Fila 2: una cabecera pulsable por columna. La primera de cada grupo lleva
              una linea a la izquierda para separar visualmente los grupos. */}
          <tr className="border-b border-border">
            {groups.flatMap((group) =>
              group.columns.map((column, index) => (
                <th
                  key={column.key}
                  aria-sort={ariaSort(sort, column)}
                  className={`border-b border-border px-2 py-1 font-medium ${index === 0 ? "border-l" : ""}`}
                >
                  <SortButton column={column} sort={sort} onSort={handleSort} />
                </th>
              )),
            )}
          </tr>
        </thead>

        <tbody>
          {sortedRows.map((row) => (
            <tr key={row.ticker} className="hover:bg-background/60">
              {/* El ticker se queda fijo a la izquierda al desplazar en horizontal (sticky). */}
              <td className="sticky left-0 z-10 border-t border-border bg-card px-2 py-1.5 font-semibold text-foreground">
                {row.ticker}
              </td>
              {groups.flatMap((group) =>
                group.columns.map((column, index) => (
                  <td
                    key={column.key}
                    className={`border-t border-border px-2 py-1.5 text-right tabular-nums ${
                      index === 0 ? "border-l" : ""
                    } ${cellClass(column, row[column.key])}`}
                  >
                    {cellText(column, row[column.key])}
                  </td>
                )),
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ScreenerTable;
