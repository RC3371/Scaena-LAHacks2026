import { useMemo } from "react";
import type { AgentEvent, AgentStatus } from "../types";

function toStatus(eventType?: string): AgentStatus {
  if (!eventType) return "idle";
  if (eventType === "error") return "error";
  if (["working", "thinking", "pitch_generating"].includes(eventType)) return "working";
  if (["complete", "insight", "pitch_ready", "followup_ready", "rebook_ready"].includes(eventType)) return "complete";
  return "idle";
}

export function useAgentEvents(events: AgentEvent[]) {
  return useMemo(() => {
    const latestByAgent = events.reduce<Record<string, AgentEvent>>((acc, event) => {
      if (!acc[event.agent_id]) acc[event.agent_id] = event;
      return acc;
    }, {});

    const statuses = {
      agent1: toStatus(latestByAgent.agent1?.event_type),
      agent2: toStatus(latestByAgent.agent2?.event_type),
      agent3: toStatus(latestByAgent.agent3?.event_type),
      agent4: toStatus(latestByAgent.agent4?.event_type),
    };

    return { latestByAgent, statuses };
  }, [events]);
}
