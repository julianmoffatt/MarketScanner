const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Una sola funcion que sabe hablar con /screeners/<nombre>/<universo>.
// Cada screener nuevo que anada el backend solo necesita una funcion publica mas abajo.
async function fetchScreener(path) {
  const response = await fetch(`${API_URL}/screeners/${path}`);
  if (!response.ok) {
    // El backend explica el motivo en "detail" (por ejemplo, "Universo 'x' no existe...").
    const body = await response.json().catch(() => null);
    throw new Error(typeof body?.detail === "string" ? body.detail : `Error ${response.status}`);
  }
  return response.json();
}

export function getMeanReversionScreener(universe) {
  return fetchScreener(`mean_reversion/${universe}`);
}
