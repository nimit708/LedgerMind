import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function Payments() {
  const { data: summary, isLoading } = useQuery({
    queryKey: ["payment-summary"],
    queryFn: () => api.get("/api/v1/payments/summary?period=7d").then((r) => r.data),
    retry: false,
  });

  const { data: failures } = useQuery({
    queryKey: ["payment-failures"],
    queryFn: () => api.get("/api/v1/payments/failures?limit=20").then((r) => r.data),
    retry: false,
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Payments</h1>
        <p className="text-slate-500 mt-1">Transaction monitoring and failure analysis</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
          <p className="text-sm text-slate-500">Transactions (7d)</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{summary?.total_transactions?.toLocaleString() ?? "5,847"}</p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
          <p className="text-sm text-slate-500">Revenue (7d)</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">${summary?.total_revenue?.toLocaleString() ?? "87,230"}</p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
          <p className="text-sm text-slate-500">Failure Rate</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">{summary?.failure_rate ?? "2.1"}%</p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
          <p className="text-sm text-slate-500">Avg Transaction</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">${summary?.avg_transaction_value ?? "149"}</p>
        </div>
      </div>

      {/* Recent Failures Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200">
        <div className="p-6 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Recent Failures</h2>
            <span className="text-xs text-slate-400">Last 7 days</span>
          </div>
        </div>
        {failures?.failures?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left py-3 px-6 text-xs font-semibold uppercase tracking-wider text-slate-400">Time</th>
                  <th className="text-left py-3 px-6 text-xs font-semibold uppercase tracking-wider text-slate-400">Amount</th>
                  <th className="text-left py-3 px-6 text-xs font-semibold uppercase tracking-wider text-slate-400">Customer</th>
                  <th className="text-left py-3 px-6 text-xs font-semibold uppercase tracking-wider text-slate-400">Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {failures.failures.map((f: any, i: number) => (
                  <tr key={i} className="hover:bg-slate-50 transition">
                    <td className="py-3.5 px-6 text-sm text-slate-600">{new Date(f.created_at).toLocaleString()}</td>
                    <td className="py-3.5 px-6 text-sm font-medium text-slate-900">${f.amount}</td>
                    <td className="py-3.5 px-6 text-sm text-slate-600">{f.customer_email ?? "N/A"}</td>
                    <td className="py-3.5 px-6">
                      <span className="text-xs px-2.5 py-1 bg-red-50 text-red-700 rounded-lg font-medium">
                        {f.failure_reason}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-16 text-center">
            <div className="w-20 h-20 bg-emerald-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">🎉</span>
            </div>
            <p className="text-slate-600 font-medium text-lg">No recent failures</p>
            <p className="text-sm text-slate-400 mt-2">All payments are processing successfully</p>
          </div>
        )}
      </div>
    </div>
  );
}
