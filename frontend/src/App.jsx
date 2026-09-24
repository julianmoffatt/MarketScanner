import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import RootLayout from "./layouts/RootLayout";
import AnalyticsLayout from "./layouts/AnalyticsLayout";
import MeanReversionDistance from "./features/analytics/pages/MeanReversionDistance";
import MeanReversionTimeAway from "./features/analytics/pages/MeanReversionTimeAway";
import DeviationCandles from "./features/analytics/pages/DeviationCandles";
import DeviationEmaTrend from "./features/analytics/pages/DeviationEmaTrend";
import StrikesCandles from "./features/analytics/pages/StrikesCandles";
import TrendDuration from "./features/analytics/pages/TrendDuration";
import Rsi from "./features/analytics/pages/Rsi";
import QuarterPatterns from "./features/analytics/pages/QuarterPatterns";
import MLHome from "./features/ml/pages/MLHome";

const DEFAULT_TICKER = "BTC";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RootLayout />}>
          <Route index element={<Navigate to="/analytics" replace />} />

          <Route
            path="analytics"
            element={<Navigate to={`/analytics/${DEFAULT_TICKER}/mean-reversion-distance?mode=lt`} replace />}
          />

          <Route path="analytics/:ticker" element={<AnalyticsLayout />}>
            <Route path="mean-reversion-distance" element={<MeanReversionDistance />} />
            <Route path="mean-reversion-time-away" element={<MeanReversionTimeAway />} />
            <Route path="deviation-candles" element={<DeviationCandles />} />
            <Route path="deviation-ema-trend" element={<DeviationEmaTrend />} />
            <Route path="strikes-candles" element={<StrikesCandles />} />
            <Route path="trend-duration" element={<TrendDuration />} />
            <Route path="rsi" element={<Rsi />} />
            <Route path="quarter-patterns" element={<QuarterPatterns />} />
          </Route>

          <Route path="ml" element={<MLHome />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
