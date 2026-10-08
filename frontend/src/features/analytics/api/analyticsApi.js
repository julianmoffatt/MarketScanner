const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function fetchAnalytics(path) {
  const response = await fetch(`${API_URL}/analytics/${path}`);
  if (!response.ok) {
    throw new Error(`Error ${response.status}`);
  }
  return response.json();
}

export function getHome(ticker) {
  return fetchAnalytics(`${ticker}/home_statistics`);
}

export function getMeanReversion_Distance_LT(ticker) {
  return fetchAnalytics(`${ticker}/mean_reversion_extension_to_mean_lt`);
}

export function getMeanReversion_Distance_HT(ticker) {
  return fetchAnalytics(`${ticker}/mean_reversion_extension_to_mean_ht`);
}

export function getMeanReversion_Distance_Macro(ticker) {
  return fetchAnalytics(`${ticker}/mean_reversion_extension_to_mean_macro`);
}

export function getMeanReversion_TimeAway_HT(ticker) {
  return fetchAnalytics(`${ticker}/mean_reversion_time_away_ht`);
}

export function getMeanReversion_TimeAway_Macro(ticker) {
  return fetchAnalytics(`${ticker}/mean_reversion_time_away_macro`);
}

export function getDeviationCandles(ticker) {
  return fetchAnalytics(`${ticker}/deviations_candle`);
}

export function getDeviationEmaTrend(ticker) {
  return fetchAnalytics(`${ticker}/deviation_ema_trend`);
}

export function getStrikesCandles(ticker) {
  return fetchAnalytics(`${ticker}/strikes_candles`);
}

export function getTrendDuration(ticker) {
  return fetchAnalytics(`${ticker}/trend_duration`);
}

export function getRsi(ticker) {
  return fetchAnalytics(`${ticker}/rsi`);
}

export function getQuarterPatterns(ticker) {
  return fetchAnalytics(`${ticker}/quarter_patterns`);
}
