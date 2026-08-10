import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function Audit() {
  const { data, isLoading } = useQuery({
    queryKey: ["audit-events"],
    queryFn: () => api.get("/api/v1/audit/events?limit=50").then((r) => r.data),
    refetchInterval: 15000,
    retry: false,
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Audit Trail</h1>
        <p className="text-slate-500 mt-1">
          Complete activity log — every agent action, user decision, and system event
        </p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <button className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-medium">All Events</button>
        <button className="px-4 py-2 bg-white border border-slate-200 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-50">Agent</button>
        <button className="px-4 py-2 bg-white border border-slate-200 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-50">User</button>
        <button className="px-4 py-2 bg-white border border-slate-200 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-50">System</button>
      </div>

      {/* Events */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200">
        {isLoading ? (
          <div className="p-12 text-center">
            <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-slate-500">Loading audit trail...</p>
          </div>
        ) : data?.events?.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {data.events.map((event: any, i: number) => (
              <div key={i} className="p-5 flex items-start gap-4 hover:bg-slate-50 transition">
                <div className={`w-3 h-3 mt-1.5 rounded-full ring-4 ${
                  event.actor === "agent" ? "bg-indigo-500 ring-indigo-50" :
                  event.actor?.startsWith("user") ? "bg-emerald-500 ring-emerald-50" : "bg-slate-400 ring-slate-50"
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start gap-4">
                    <p className="font-medium text-sm text-slate-900">{event.description}</p>
                    <span className="text-xs text-slate-400 whitespace-nowrap">
                      {new Date(event.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex gap-2 mt-2">
                    <span className="text-xs px-2.5 py-1 bg-slate-100 text-slate-600 rounded-lg font-medium">
                      {event.event_type}
                    </span>
                    <span className="text-xs px-2.5 py-1 bg-slate-100 text-slate-600 rounded-lg">
                      {event.actor}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-16 text-center">
            <div className="w-20 h-20 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">📋</span>
            </div>
            <p className="text-slate-600 font-medium text-lg">No audit events yet</p>
            <p className="text-sm text-slate-400 mt-2 max-w-sm mx-auto">
              Activity will appear here as the agent operates. Try chatting with the AI agent to generate events.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
