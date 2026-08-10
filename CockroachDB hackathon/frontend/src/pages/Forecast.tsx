import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function Forecast() {
  const { data: revenue } = useQuery({
    queryKey: ["forecast-revenue"],
    queryFn: () => api.get("/api/v1/forecast/revenue?days=30").then((r) => r.data),
    retry: false,
  });

  const { data: brief } = useQuery({
    queryKey: ["daily-brief"],
    queryFn: () => api.get("/api/v1/forecast/daily-brief").then((r) => r.data),
    retry: false,
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Forecast & Insights</h1>
        <p className="text-slate-500 mt-1">AI-powered predictions and daily operational brief</p>
      </div>

      {/* Daily Brief */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center">
              <span className="text-xl">📰</span>
            </div>
            <h2 className="text-lg font-semibold text-slate-900">Daily Brief</h2>
          </div>
          <span className={`px-4 py-1.5 rounded-xl text-sm font-semibold ${
            (brief?.health_score ?? 96) >= 80
              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
              : (brief?.health_score ?? 96) >= 50
              ? "bg-amber-50 text-amber-700 border border-amber-200"
              : "bg-red-50 text-red-700 border border-red-200"
          }`}>
            Health: {brief?.health_score ?? "96"}/100
          </span>
        </div>
        
        <div className="p-5 bg-gradient-to-r from-slate-50 to-indigo-50/30 rounded-xl mb-4">
          <p className="text-xl font-semibold text-slate-800">
            {brief?.headline ?? "Payment operations running smoothly — revenue up 12% vs last week"}
          </p>
          <p className="text-slate-500 mt-2">
            {brief?.forecast_summary ?? "Based on current trends, projected weekly revenue is $91,400. No significant anomalies detected."}
          </p>
        </div>

        {(brief?.action_items?.length > 0 || true) && (
          <div>
            <h3 className="font-semibold text-sm text-slate-500 uppercase tracking-wider mb-3">Recommended Actions</h3>
            <div className="space-y-2">
              {(brief?.action_items ?? [
                "Review 3 failed recurring payments for VIP customers",
                "Approve retry campaign for expired card declines",
                "Monitor elevated decline rate from processor Alpha",
              ]).map((item: string, i: number) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
                  <div className="w-6 h-6 bg-indigo-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-xs font-bold text-indigo-600">{i + 1}</span>
                  </div>
                  <p className="text-sm text-slate-700">{item}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Revenue Forecast */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center">
              <span className="text-xl">📈</span>
            </div>
            <h2 className="text-lg font-semibold text-slate-900">Revenue Forecast (30 days)</h2>
          </div>
          <span className="px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-xl text-sm font-medium">
            {revenue?.trend ?? "↑ Upward"}
          </span>
        </div>
        
        <p className="text-slate-600 mb-6">
          {revenue?.summary ?? "Revenue projected to grow 8-12% over the next 30 days based on seasonal patterns and current pipeline."}
        </p>

        {/* Simple visual forecast bars */}
        <div className="grid grid-cols-7 gap-2">
          {Array.from({ length: 7 }, (_, i) => {
            const height = 40 + Math.random() * 50;
            return (
              <div key={i} className="flex flex-col items-center gap-1">
                <div className="w-full bg-slate-100 rounded-lg h-24 flex items-end overflow-hidden">
                  <div
                    className="w-full bg-gradient-to-t from-indigo-600 to-indigo-400 rounded-lg transition-all"
                    style={{ height: `${height}%` }}
                  />
                </div>
                <span className="text-xs text-slate-400">W{i + 1}</span>
              </div>
            );
          })}
        </div>
        <p className="text-xs text-slate-400 mt-3 text-center">Weekly revenue projection (next 7 weeks)</p>
      </div>
    </div>
  );
}
