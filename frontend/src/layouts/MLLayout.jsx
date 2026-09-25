import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useTicker } from "../features/analytics/hooks/useTicker";

const TABS = [
  { path: "training", label: "Training" },
  { path: "prediction", label: "Prediction" },
];

function MLLayout() {
  const { ticker, setTicker } = useTicker();
  const [input, setInput] = useState(ticker);

  useEffect(() => {
    setInput(ticker);
  }, [ticker]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setTicker(input);
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="border-b border-border">
        <div className="relative flex items-center justify-end gap-6 px-6 py-4">
          <nav className="absolute left-1/2 flex -translate-x-1/2 gap-6">
            {TABS.map((tab) => (
              <NavLink
                key={tab.path}
                to={`/ml/${ticker}/${tab.path}`}
                className={({ isActive }) =>
                  `whitespace-nowrap border-b-2 py-3 text-sm font-medium transition-colors ${
                    isActive
                      ? "border-gold text-gold"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`
                }
              >
                {tab.label}
              </NavLink>
            ))}
          </nav>

          <form onSubmit={handleSubmit} className="flex items-center gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="w-28 rounded-md border border-border bg-card px-3 py-1.5 text-sm text-foreground outline-none focus:border-gold"
            />
            <button
              type="submit"
              className="rounded-md border border-gold px-3 py-1.5 text-sm font-medium text-gold transition-colors hover:bg-gold hover:text-background"
            >
              Change
            </button>
          </form>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 flex-col px-6 py-3">
        <Outlet />
      </div>
    </div>
  );
}

export default MLLayout;
