const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Borra los CSV descargados (raw y processed) y las caches del backend. No
// descarga nada: los datos se bajan de Yahoo Finance al volver a pedirlos.
export async function clearDataCache() {
  const response = await fetch(`${API_URL}/data-cache/clear`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Error ${response.status}`);
  }
  return response.json();
}
