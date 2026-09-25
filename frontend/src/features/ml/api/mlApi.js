const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function fetchML(path, { signal } = {}) {
  const response = await fetch(`${API_URL}/ml/${path}`, { signal });
  if (!response.ok) {
    throw new Error(`Error ${response.status}`);
  }
  return response.json();
}

export function getMLTraining(ticker, options) {
  return fetchML(`${ticker}/training`, options);
}

export function getMLPrediction(ticker, options) {
  return fetchML(`${ticker}/prediction`, options);
}
