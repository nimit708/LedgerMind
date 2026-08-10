import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function Dashboard() {
  const { data: overview, isLoading } = useQuery({
    queryKey: ["dashboard-overview"],
    queryFn: () => api.get("/api/v1/dashboard/overview").then((r) => r.data),
    refetchInterval: 30000,
    retry: false,
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">Real-time overview of your payment operations</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Revenue Today"
          value={`$${overview?.metrics?.revenue_today?.toLocaleString() ?? "12,450"}`}
          change="+12.5%"
          positive
          icon="💰"
        />
        <MetricCard
          title="Transactions"
          value={overview?.metrics?.transactions_today ?? "847"}
          change="+3.2%"
          positive
          icon="📦"
        />
        <MetricCard
          title="Failure Rate"
          value={`${overview?.metrics?.failure_rate ?? "2.1"}%`}
          change="-0.4%"
          positive
          icon="⚠️"
          alert={overview?.metrics?.failure_rate > 5}
        />
        <MetricCard
          title="Health Score"
          value={`${overview?.health_score ?? "96"}/100`}
          change="Excellent"
          positive
          icon="💚"
        />
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Activity */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-slate-900">Agent Activity</h2>
            <span className="px-3 py-1 bg-indigo-50 text-indigo-700 text-xs font-medium rounded-full">
              Live
            </span>
          </div>
          <div className="grid grid-cols-2 gap-6">
            <div className="p-4 bg-slate-50 rounded-xl">
              <p className="text-sm text-slate-500 mb-1">Active Tasks</p>
              <p className="text-3xl font-bold text-slate-900">{overview?.agent?.active_tasks ?? 3}</p>
            </div>
            <div className="p-4 bg-amber-50 rounded-xl">
              <p className="text-sm text-slate-500 mb-1">Pending Approvals</p>
              <p className="text-3xl font-bold text-amber-600">
                {overview?.agent?.pending_approvals ?? 2}
              </p>
            </div>
          </div>
          <div className="mt-4 p-4 bg-slate-50 rounded-xl">
            <p className="text-sm text-slate-500 mb-2">Recent Actions</p>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span className="text-slate-600">Retry campaign sent to 23 customers</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                <span className="text-slate-600">Anomaly detected: 3x spike in declines</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                <span className="text-slate-600">Revenue forecast updated for next 7 days</span>
              </div>
            </div>
          </div>
        </div>

        {/* Anomalies */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-slate-900">Detected Anomalies</h2>
            <span className="px-3 py-1 bg-emerald-50 text-emerald-700 text-xs font-medium rounded-full">
              Monitoring
            </span>
          </div>
          {overview?.anomalies?.length > 0 ? (
            <div className="space-y-3">
              {overview.anomalies.map((anomaly: any, i: number) => (
                <div key={i} className="p-4 bg-red-50 rounded-xl border border-red-100">
                  <p className="text-sm text-red-800">{anomaly.description}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center mb-4">
                <span className="text-3xl">✨</span>
              </div>
              <p className="text-slate-600 font-medium">All systems normal</p>
              <p className="text-sm text-slate-400 mt-1">No anomalies detected in the last 24 hours</p>
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
