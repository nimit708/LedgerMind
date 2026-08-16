import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function Dashboard() {
  const { data: overview } = useQuery({
    queryKey: ["dashboard-overview"],
    queryFn: () => api.get("/api/v1/dashboard/overview").then((r) => r.data),
    refetchInterval: 30000,
    retry: false,
  });

  const { data: brief, isLoading: briefLoading } = useQuery({
    queryKey: ["daily-brief"],
    queryFn: () => api.get("/api/v1/dashboard/daily-brief").then((r) => r.data),
    refetchInterval: 60000,
    retry: false,
  });

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="space-y-6">
      {/* Daily Brief Card */}
      <div className={`rounded-2xl p-6 shadow-sm border ${
        brief?.health === "needs_attention" ? "bg-red-50 border-red-200" :
        brief?.health === "warning" ? "bg-amber-50 border-amber-200" :
        brief?.health === "excellent" ? "bg-emerald-50 border-emerald-200" :
        "bg-white border-slate-200"
      }`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm text-slate-500 font-medium">{greeting()} — here's your daily brief</p>
            <h1 className="text-2xl font-bold text-slate-900 mt-1">
              {briefLoading ? "Loading your brief..." : brief?.headline ?? "Loading..."}
            </h1>
          </div>
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl ${
            (brief?.health_score ?? 85) >= 85 ? "bg-emerald-100 text-emerald-800" :
            (brief?.health_score ?? 85) >= 70 ? "bg-amber-100 text-amber-800" :
            "bg-red-100 text-red-800"
          }`}>
            <span className="text-lg font-bold">{brief?.health_score ?? "--"}</span>
            <span className="text-xs font-medium">/100</span>
          </div>
        </div>

        {/* Quick Metrics Row */}
        {brief?.metrics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
            <div className="bg-white/70 rounded-xl p-3 backdrop-blur-sm">
              <p className="text-xs text-slate-500">Revenue Today</p>
              <p className="text-lg font-bold text-slate-900">${brief.metrics.revenue_today?.toLocaleString(undefined, {maximumFractionDigits: 0}) ?? "0"}</p>
              <p className={`text-xs font-medium mt-0.5 ${brief.metrics.revenue_change_pct >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                {brief.metrics.revenue_change_pct >= 0 ? "↑" : "↓"} {Math.abs(brief.metrics.revenue_change_pct ?? 0)}% vs yesterday
              </p>
            </div>
            <div className="bg-white/70 rounded-xl p-3 backdrop-blur-sm">
              <p className="text-xs text-slate-500">Payments</p>
              <p className="text-lg font-bold text-slate-900">{brief.metrics.transactions_succeeded ?? 0} <span className="text-sm font-normal text-slate-400">/ {brief.metrics.transactions_total ?? 0}</span></p>
              <p className="text-xs text-emerald-600 font-medium mt-0.5">{brief.metrics.success_rate ?? 100}% success</p>
            </div>
            <div className="bg-white/70 rounded-xl p-3 backdrop-blur-sm">
              <p className="text-xs text-slate-500">Failed</p>
              <p className={`text-lg font-bold ${(brief.metrics.transactions_failed ?? 0) > 3 ? "text-red-600" : "text-slate-900"}`}>{brief.metrics.transactions_failed ?? 0}</p>
              <p className="text-xs text-red-600 font-medium mt-0.5">${brief.metrics.revenue_at_risk?.toLocaleString(undefined, {maximumFractionDigits: 0}) ?? "0"} at risk</p>
            </div>
            <div className="bg-white/70 rounded-xl p-3 backdrop-blur-sm">
              <p className="text-xs text-slate-500">New Customers</p>
              <p className="text-lg font-bold text-slate-900">{brief.metrics.new_customers ?? 0}</p>
              <p className="text-xs text-slate-400 font-medium mt-0.5">today</p>
            </div>
          </div>
        )}

        {/* Action Items */}
        {brief?.action_items && brief.action_items.length > 0 && (
          <div className="mt-5 space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Action Items</p>
            {brief.action_items.map((item: any, i: number) => (
              <div key={i} className={`flex items-center justify-between p-3 rounded-xl ${
                item.priority === "high" ? "bg-red-100/60 border border-red-200" :
                item.priority === "medium" ? "bg-amber-100/60 border border-amber-200" :
                "bg-slate-100/60 border border-slate-200"
              }`}>
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    item.priority === "high" ? "bg-red-500" :
                    item.priority === "medium" ? "bg-amber-500" :
                    "bg-emerald-500"
                  }`} />
                  <span className="text-sm text-slate-700">{item.action}</span>
                </div>
                <span className="text-xs font-medium text-indigo-600 whitespace-nowrap">{item.cta} →</span>
              </div>
            ))}
          </div>
        )}

        {/* Top Failures Today */}
        {brief?.top_failures && brief.top_failures.length > 0 && (
          <div className="mt-4 flex items-center gap-3 flex-wrap">
            <span className="text-xs text-slate-500">Top failures:</span>
            {brief.top_failures.map((f: any, i: number) => (
              <span key={i} className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-lg font-medium">
                {f.reason} ({f.count})
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Revenue (7d)"
          value={`$${overview?.metrics?.revenue_today ? (overview.metrics.revenue_today * 7).toLocaleString(undefined, {maximumFractionDigits: 0}) : "0"}`}
          change={`${brief?.metrics?.revenue_change_pct >= 0 ? "+" : ""}${brief?.metrics?.revenue_change_pct ?? 0}%`}
          positive={(brief?.metrics?.revenue_change_pct ?? 0) >= 0}
          icon="💰"
        />
        <MetricCard
          title="Transactions Today"
          value={overview?.metrics?.transactions_today ?? brief?.metrics?.transactions_total ?? 0}
          change={`${brief?.metrics?.success_rate ?? 100}% success`}
          positive={(brief?.metrics?.success_rate ?? 100) > 90}
          icon="📦"
        />
        <MetricCard
          title="Failure Rate"
          value={`${overview?.metrics?.failure_rate ?? "0"}%`}
          change={(overview?.metrics?.failure_rate ?? 0) < 5 ? "Normal" : "Elevated"}
          positive={(overview?.metrics?.failure_rate ?? 0) < 5}
          icon="⚠️"
          alert={(overview?.metrics?.failure_rate ?? 0) > 5}
        />
        <MetricCard
          title="Pending Actions"
          value={brief?.pending_approvals ?? overview?.agent?.pending_approvals ?? 0}
          change={brief?.pending_approvals > 0 ? "Needs review" : "All clear"}
          positive={(brief?.pending_approvals ?? 0) === 0}
          icon="📋"
        />
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weekly Revenue Trend */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Revenue Trend (7 Days)</h2>
          {brief?.weekly_trend && brief.weekly_trend.length > 0 ? (
            <div className="space-y-2">
              {brief.weekly_trend.map((day: any, i: number) => {
                const maxRev = Math.max(...brief.weekly_trend.map((d: any) => d.revenue));
                const pct = maxRev > 0 ? (day.revenue / maxRev) * 100 : 0;
                return (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-xs text-slate-400 w-20">{new Date(day.day).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}</span>
                    <div className="flex-1 h-6 bg-slate-100 rounded-lg overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-lg flex items-center justify-end pr-2"
                        style={{ width: `${Math.max(pct, 5)}%` }}
                      >
                        {pct > 30 && <span className="text-xs text-white font-medium">${day.revenue.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>}
                      </div>
                    </div>
                    {pct <= 30 && <span className="text-xs text-slate-500">${day.revenue.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-400 text-center py-8">No revenue data yet</p>
          )}
        </div>

        {/* Affected Customers */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Customers Needing Attention</h2>
          {brief?.affected_customers && brief.affected_customers.length > 0 ? (
            <div className="space-y-3">
              {brief.affected_customers.map((name: string, i: number) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-red-50 rounded-xl border border-red-100">
                  <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                    <span className="text-sm">⚠️</span>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-800">{name}</p>
                    <p className="text-xs text-red-600">Payment failed today</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center mb-4">
                <span className="text-3xl">✅</span>
              </div>
              <p className="text-slate-600 font-medium">All customers healthy</p>
              <p className="text-sm text-slate-400 mt-1">No payment issues detected today</p>
            </div>
          )}
        </div>
      </div>

      {/* CockroachDB Info Banner */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-6 text-white shadow-lg shadow-indigo-500/20">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
            <span className="text-2xl">🧠</span>
          </div>
          <div>
            <h3 className="font-semibold text-lg">Powered by CockroachDB + Amazon Bedrock</h3>
            <p className="text-indigo-100 text-sm mt-0.5">
              Distributed agentic memory with human-in-the-loop AI reasoning for payment operations
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  title,
  value,
  change,
  positive,
  icon,
  alert = false,
}: {
  title: string;
  value: string | number;
  change: string;
  positive: boolean;
  icon: string;
  alert?: boolean;
}) {
  return (
    <div className={`bg-white rounded-2xl shadow-sm border p-5 ${alert ? "border-red-200" : "border-slate-200"}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-2xl">{icon}</span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
          positive ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
        }`}>
          {change}
        </span>
      </div>
      <p className="text-sm text-slate-500 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${alert ? "text-red-600" : "text-slate-900"}`}>{value}</p>
    </div>
  );
}
