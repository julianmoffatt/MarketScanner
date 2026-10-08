const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// El backend manda el motivo en "detail": un texto (errores del motor) o una
// lista de objetos {loc, msg} (validacion de pydantic).
function formatDetail(detail, status) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => `${(d.loc ?? []).slice(1).join(".")}: ${d.msg}`).join("; ");
  }
  return `Error ${status}`;
}

export async function runBacktest(request, { signal } = {}) {
  const response = await fetch(`${API_URL}/backtesting/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(formatDetail(body?.detail, response.status));
  }
  return response.json();
}
