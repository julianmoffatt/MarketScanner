import { NavLink, Outlet } from "react-router-dom";
import avatar from "../assets/avatar.png";

const SECTIONS = [
  { to: "/analytics", label: "Statistics" },
  { to: "/ml", label: "Machine Learning" },
  { to: "/backtesting", label: "Backtesting" },
];

function RootLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="border-b border-border">
        <div className="relative flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-2 whitespace-nowrap">
            <span className="text-xl font-bold text-gold">/</span>
            <span className="text-sm font-semibold tracking-[0.25em] text-foreground">
              MARKET SCANNER
            </span>
            <span className="text-xl font-bold text-gold">/</span>
          </div>

          <nav className="absolute left-1/2 flex -translate-x-1/2 gap-10">
            {SECTIONS.map((section) => (
              <NavLink
                key={section.to}
                to={section.to}
                className={({ isActive }) =>
                  `border-b-2 pb-1 text-sm font-medium transition-colors ${
                    isActive
                      ? "border-gold text-gold"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`
                }
              >
                {section.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-foreground">Julian Moffatt</span>
            <img
              src={avatar}
              alt="Julian Moffatt"
              className="h-10 w-10 shrink-0 rounded-full border border-border object-cover"
            />
          </div>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 flex-col">
        <Outlet />
      </div>
    </div>
  );
}

export default RootLayout;
