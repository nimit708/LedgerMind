import { Link, useLocation } from "react-router-dom";
import { ReactNode } from "react";

interface LayoutProps {
  children: ReactNode;
  user: any;
  onSignOut: (() => void) | undefined;
}

const navItems = [
  { path: "/", label: "Dashboard", icon: "📊" },
  { path: "/agent", label: "AI Agent", icon: "🤖" },
  { path: "/approvals", label: "Approvals", icon: "✅" },
  { path: "/payments", label: "Payments", icon: "💳" },
  { path: "/forecast", label: "Forecast", icon: "📈" },
  { path: "/audit", label: "Audit Trail", icon: "📋" },
];

export function Layout({ children, user, onSignOut }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Sidebar */}
      <aside className="w-72 bg-slate-900 text-white flex flex-col shadow-2xl">
        {/* Logo */}
        <div className="p-6 border-b border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-lg font-bold shadow-lg shadow-indigo-500/25">
              L
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">LedgerMind</h1>
              <p className="text-xs text-slate-400">AI Payment Operations</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          <p className="text-xs uppercase tracking-wider text-slate-500 font-semibold px-3 mb-3">
            Navigation
          </p>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                  isActive
                    ? "bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-lg shadow-indigo-600/30"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                <span className="font-medium text-sm">{item.label}</span>
                {isActive && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Status indicator */}
        <div className="px-4 py-3">
          <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-slate-400">System Status</span>
            </div>
            <p className="text-xs text-emerald-400 font-medium">All services operational</p>
          </div>
        </div>

        {/* User section */}
        <div className="p-4 border-t border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-sm font-bold">
              {user?.username?.charAt(0)?.toUpperCase() || "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-200 truncate">
                {user?.username || "User"}
              </p>
              <button
                onClick={onSignOut}
                className="text-xs text-slate-400 hover:text-red-400 transition-colors"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
