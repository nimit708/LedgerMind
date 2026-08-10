import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

export function Approvals() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["pending-approvals"],
    queryFn: () => api.get("/api/v1/approvals/pending").then((r) => r.data),
    refetchInterval: 10000,
    retry: false,
  });

  const decideMutation = useMutation({
    mutationFn: ({ id, status, reason }: { id: string; status: string; reason?: string }) =>
      api.post(`/api/v1/approvals/${id}/decide`, { status, reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pending-approvals"] });
    },
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Approvals</h1>
        <p className="text-slate-500 mt-1">
          Review and approve AI-recommended actions before execution
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <p className="text-sm text-slate-500">Pending</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">{data?.approvals?.length ?? 0}</p>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <p className="text-sm text-slate-500">Approved Today</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">12</p>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <p className="text-sm text-slate-500">Rejected Today</p>
          <p className="text-2xl font-bold text-red-600 mt-1">1</p>
        </div>
      </div>

      {/* Approvals List */}
      {isLoading ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-sm">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-500">Loading approvals...</p>
        </div>
      ) : data?.approvals?.length > 0 ? (
        <div className="space-y-4">
          {data.approvals.map((approval: any) => (
            <div key={approval.id} className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg text-slate-900">{approval.summary}</h3>
                  <p className="text-slate-500 mt-1 text-sm">{approval.explanation}</p>
                </div>
                <span
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold ${
                    approval.risk_level === "high"
                      ? "bg-red-50 text-red-700 border border-red-200"
                      : approval.risk_level === "medium"
                      ? "bg-amber-50 text-amber-700 border border-amber-200"
                      : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                  }`}
                >
                  {approval.risk_level} risk
                </span>
              </div>

              <div className="mt-4 p-4 bg-slate-50 rounded-xl">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Proposed Action</p>
                <p className="text-sm text-slate-700">{approval.proposed_action}</p>
              </div>

              <div className="mt-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-indigo-600 rounded-full"
                        style={{ width: `${(approval.confidence ?? 0.85) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-slate-500">
                      {((approval.confidence ?? 0.85) * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => decideMutation.mutate({ id: approval.id, status: "approved" })}
                    className="px-5 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700 shadow-sm transition"
                  >
                    ✓ Approve
                  </button>
                  <button
                    onClick={() => decideMutation.mutate({ id: approval.id, status: "rejected" })}
                    className="px-5 py-2.5 bg-white border border-red-200 text-red-600 rounded-xl text-sm font-medium hover:bg-red-50 transition"
                  >
                    ✕ Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-16 text-center">
          <div className="w-20 h-20 bg-emerald-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-4xl">✅</span>
          </div>
          <p className="text-slate-600 font-medium text-lg">All caught up!</p>
          <p className="text-sm text-slate-400 mt-2 max-w-sm mx-auto">
            No pending approvals. The agent will notify you when actions need your review.
          </p>
        </div>
      )}
    </div>
  );
}
