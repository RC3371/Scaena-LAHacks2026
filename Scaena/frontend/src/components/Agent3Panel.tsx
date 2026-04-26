import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis } from "recharts";
import type { Conversation, Insight } from "../types";
import { InsightCard } from "./InsightCard";
import { ThinkingIndicator } from "./ThinkingIndicator";

export function Agent3Panel({
  thinkingSteps,
  conversations,
  insights,
}: {
  thinkingSteps: Array<{ step: string; conclusion?: string }>;
  conversations: Conversation[];
  insights: Insight[];
}) {
  const chart = insights.slice(0, 6).reverse().map((item) => ({ round: item.round_number, price: item.optimal_price }));
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
        <h3 className="mb-2 text-white">Live Thinking</h3>
        <ThinkingIndicator steps={thinkingSteps} />
      </div>
      <div className="space-y-3 rounded-xl border border-slate-700 bg-slate-900 p-4">
        <h3 className="text-white">Insights</h3>
        <div className="grid gap-2">
          {conversations.slice(0, 4).map((c) => (
            <InsightCard key={c.id} venue={c.venue_name} interest={c.interest_level} worked={c.what_worked} nextAction={c.what_to_do_next} />
          ))}
        </div>
        <div className="h-36">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart}>
              <XAxis dataKey="round" />
              <YAxis />
              <Bar dataKey="price" fill="#22c55e" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
