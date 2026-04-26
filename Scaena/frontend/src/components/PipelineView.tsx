import { AgentNode } from "./AgentNode";
import { AgentActivityFeed } from "./AgentActivityFeed";
import type { AgentEvent, AgentStatus } from "../types";

interface PipelineViewProps {
  statuses: Record<"agent1" | "agent2" | "agent3" | "agent4", AgentStatus>;
  latestMessages: Record<string, string | undefined>;
  events: AgentEvent[];
  onSelect: (agent: "agent1" | "agent2" | "agent3" | "agent4") => void;
}

export function PipelineView({ statuses, latestMessages, events, onSelect }: PipelineViewProps) {
  return (
    <section className="space-y-4">
      <div className="grid gap-3 md:grid-cols-4">
        <AgentNode name="Agent 1: Research" status={statuses.agent1} message={latestMessages.agent1} onClick={() => onSelect("agent1")} />
        <AgentNode name="Agent 2: Pitching" status={statuses.agent2} message={latestMessages.agent2} onClick={() => onSelect("agent2")} />
        <AgentNode name="Agent 3: Learning" status={statuses.agent3} message={latestMessages.agent3} onClick={() => onSelect("agent3")} />
        <AgentNode name="Agent 4: Follow-Up" status={statuses.agent4} message={latestMessages.agent4} onClick={() => onSelect("agent4")} />
      </div>
      <AgentActivityFeed events={events} />
    </section>
  );
}
