const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function fetchML(path, { signal } = {}) {
  const response = await fetch(`${API_URL}/ml/${path}`, { signal });
  if (!response.ok) {
    // El backend manda el motivo real en el campo "detail" (ej. "Solo hay
    // 250 velas de historico..."), no solo el codigo -- si el cuerpo no es
    // JSON valido (error inesperado sin el handler de ValueError), cae al
    // mensaje generico de siempre.
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || `Error ${response.status}`);
  }
  return response.json();
}

export function getMLTraining(ticker, options) {
  return fetchML(`${ticker}/training`, options);
}

export function getMLPrediction(ticker, options) {
  return fetchML(`${ticker}/prediction`, options);
}
