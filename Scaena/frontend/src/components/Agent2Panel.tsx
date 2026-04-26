import { useMemo, useState } from "react";
import type { Conversation, Pitch } from "../types";
import { TargetCard } from "./TargetCard";
import { ConversationDrawer } from "./ConversationDrawer";
import { OutreachConfirmModal } from "./OutreachConfirmModal";

interface Agent2PanelProps {
  pitches: Pitch[];
  conversations: Record<string, Conversation>;
  outreachMode: "manual_approve" | "auto_pitch";
  onToggleMode: (mode: "manual_approve" | "auto_pitch") => Promise<void>;
  onSendPitch: (pitchId: string) => Promise<void>;
  onStrategyUpdate: (targetId: string, instruction: string) => Promise<void>;
  onLogReply: (targetId: string, reply: string) => Promise<void>;
}

export function Agent2Panel(props: Agent2PanelProps) {
  const [selectedTarget, setSelectedTarget] = useState<string | null>(null);
  const [confirmPitchId, setConfirmPitchId] = useState<string | null>(null);
  const selectedPitch = props.pitches.find((p) => p.id === confirmPitchId);
  const conversationList = useMemo(() => Object.values(props.conversations), [props.conversations]);
  const selectedConversation = useMemo(
    () => (selectedTarget ? props.conversations[selectedTarget] ?? null : null),
    [selectedTarget, props.conversations],
  );

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
        <label className="text-sm text-slate-300">Outreach Mode</label>
        <div className="mt-2 flex gap-2">
          <button onClick={() => props.onToggleMode("manual_approve")} className="rounded bg-slate-700 px-3 py-1 text-xs text-white">Manual Approve</button>
          <button onClick={() => props.onToggleMode("auto_pitch")} className="rounded bg-slate-700 px-3 py-1 text-xs text-white">Auto Pitch</button>
          <span className="text-xs text-slate-400">Current: {props.outreachMode}</span>
        </div>
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        {props.pitches.map((pitch) => (
          <div key={pitch.id} className="space-y-2">
            <TargetCard
              pitch={pitch}
              onOpen={() => {
                const conv = conversationList.find((item) => item.pitch_id === pitch.id);
                if (conv) setSelectedTarget(conv.id);
              }}
            />
            {props.outreachMode === "manual_approve" && pitch.status === "draft" ? (
              <button onClick={() => setConfirmPitchId(pitch.id)} className="rounded bg-emerald-600 px-2 py-1 text-xs text-white">
                Approve & Send
              </button>
            ) : null}
          </div>
        ))}
      </div>
      <ConversationDrawer
        conversation={selectedConversation}
        onClose={() => setSelectedTarget(null)}
        onStrategyUpdate={(instruction) => props.onStrategyUpdate(selectedTarget || "", instruction)}
        onLogReply={(reply) => props.onLogReply(selectedTarget || "", reply)}
      />
      <OutreachConfirmModal
        open={Boolean(confirmPitchId && selectedPitch)}
        subject={selectedPitch?.pitch_subject || ""}
        body={selectedPitch?.pitch_body || ""}
        onConfirm={async () => {
          if (confirmPitchId) await props.onSendPitch(confirmPitchId);
          setConfirmPitchId(null);
        }}
        onClose={() => setConfirmPitchId(null)}
      />
    </div>
  );
}
