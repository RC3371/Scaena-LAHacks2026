import type { AgentEvent } from "../types";

export function AgentActivityFeed({ events }: { events: AgentEvent[] }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 p-3">
      <h4 className="mb-2 text-sm font-semibold text-slate-100">Live Activity</h4>
      <div className="max-h-56 space-y-2 overflow-auto text-xs">
        {events.slice(0, 50).map((event, idx) => (
          <div key={`${event.agent_id}-${idx}`} className="rounded bg-slate-800 p-2 text-slate-200">
            <span className="mr-2 font-semibold uppercase">{event.agent_id}</span>
            <span className="mr-2 text-slate-400">{event.event_type}</span>
            <span>{event.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
