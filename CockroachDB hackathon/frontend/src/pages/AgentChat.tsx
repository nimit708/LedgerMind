import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../lib/api";

interface Message {
  role: "user" | "agent";
  content: string;
  requires_approval?: boolean;
  timestamp: Date;
}

export function AgentChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "agent",
      content: "Hi! I'm LedgerMind, your AI payment operations assistant. I can help you investigate payment failures, create recovery campaigns, forecast revenue, and more. What would you like to explore?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);

  const chatMutation = useMutation({
    mutationFn: (message: string) =>
      api.post("/api/v1/agent/chat", { message, conversation_id: conversationId }),
    onSuccess: (response) => {
      const data = response.data;
      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        { role: "agent", content: data.response, requires_approval: data.requires_approval, timestamp: new Date() },
      ]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        { role: "agent", content: "I'm having trouble connecting to the backend. The API service may still be starting up.", timestamp: new Date() },
      ]);
    },
  });

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content: input, timestamp: new Date() }]);
    chatMutation.mutate(input);
    setInput("");
  };

  const quickActions = [
    { label: "🔍 Investigate failure spike", task: "investigate_failure_spike" },
    { label: "🔄 Create recovery campaign", task: "create_recovery_list" },
    { label: "📧 Follow up inactive customers", task: "follow_up_inactive" },
    { label: "👁️ Monitor anomaly (24h)", task: "monitor_anomaly" },
    { label: "📊 Revenue forecast", task: "prepare_campaign" },
    { label: "⚡ Performance check", task: "schedule_performance_check" },
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900">AI Agent</h1>
        <p className="text-slate-500 mt-1">Chat with LedgerMind to manage your payment operations</p>
      </div>

      {/* Quick Actions */}
      <div className="flex flex-wrap gap-2 mb-4">
        {quickActions.map((action) => (
          <button
            key={action.task}
            onClick={() => {
              setMessages((prev) => [...prev, { role: "user", content: action.label, timestamp: new Date() }]);
              chatMutation.mutate(action.label);
            }}
            className="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-xl text-sm font-medium hover:bg-indigo-50 hover:border-indigo-200 hover:text-indigo-700 transition-all duration-200 shadow-sm"
          >
            {action.label}
          </button>
        ))}
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[75%] p-4 rounded-2xl ${
                msg.role === "user"
                  ? "bg-indigo-600 text-white rounded-br-md"
                  : "bg-slate-100 text-slate-800 rounded-bl-md"
              }`}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              {msg.requires_approval && (
                <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-xl">
                  <p className="text-sm text-amber-800 font-medium">⚠️ This action requires your approval</p>
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => {
                        setMessages((prev) => [...prev, { role: "user", content: "✅ Approved", timestamp: new Date() }]);
                        chatMutation.mutate("I approve this action. Please proceed.");
                      }}
                      className="px-4 py-1.5 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition cursor-pointer"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => {
                        setMessages((prev) => [...prev, { role: "user", content: "❌ Rejected", timestamp: new Date() }]);
                        chatMutation.mutate("I reject this action. Do not proceed.");
                      }}
                      className="px-4 py-1.5 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition cursor-pointer"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              )}
              <p className={`text-xs mt-2 ${msg.role === "user" ? "text-indigo-200" : "text-slate-400"}`}>
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}
        {chatMutation.isPending && (
          <div className="flex justify-start">
            <div className="bg-slate-100 p-4 rounded-2xl rounded-bl-md">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask about payment failures, revenue trends, or schedule tasks..."
          className="flex-1 px-5 py-3.5 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-sm transition"
        />
        <button
          onClick={handleSend}
          disabled={chatMutation.isPending}
          className="px-6 py-3.5 bg-indigo-600 text-white rounded-xl font-medium text-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm shadow-indigo-600/20 transition"
        >
          Send
        </button>
      </div>
    </div>
  );
}
