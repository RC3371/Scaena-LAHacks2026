import { useState } from "react";
import type { Conversation } from "../types";

interface ConversationDrawerProps {
  conversation: Conversation | null;
  onClose: () => void;
  onStrategyUpdate: (instruction: string) => Promise<void>;
  onLogReply: (reply: string) => Promise<void>;
}

export function ConversationDrawer({ conversation, onClose, onStrategyUpdate, onLogReply }: ConversationDrawerProps) {
  const [instruction, setInstruction] = useState("");
  const [reply, setReply] = useState("");
  if (!conversation) return null;

  return (
    <aside className="fixed right-0 top-0 z-40 h-full w-full max-w-xl overflow-auto border-l border-slate-700 bg-slate-950 p-4">
      <div className="mb-4 flex items-center justify-between">
        <h4 className="text-lg font-semibold text-white">{conversation.venue_name}</h4>
        <button onClick={onClose} className="text-sm text-slate-300">Close</button>
      </div>
      <div className="space-y-2">
        {conversation.messages.map((m) => (
          <div key={m.id} className={`rounded p-2 text-sm ${m.direction === "outbound" ? "bg-blue-900/50 text-blue-100" : "bg-slate-800 text-slate-100"}`}>
            <div className="mb-1 text-xs uppercase opacity-70">{m.message_type}</div>
            <div>{m.body}</div>
          </div>
        ))}
      </div>
      <div className="mt-4 space-y-2">
        <textarea value={instruction} onChange={(e) => setInstruction(e.target.value)} placeholder="Change strategy for this target..." className="w-full rounded bg-slate-800 p-2 text-sm text-white" />
        <button onClick={() => onStrategyUpdate(instruction)} className="rounded bg-indigo-600 px-3 py-2 text-sm text-white">Request Rewrite</button>
      </div>
      <div className="mt-4 space-y-2">
        <textarea value={reply} onChange={(e) => setReply(e.target.value)} placeholder="Log venue reply..." className="w-full rounded bg-slate-800 p-2 text-sm text-white" />
        <button onClick={() => onLogReply(reply)} className="rounded bg-emerald-600 px-3 py-2 text-sm text-white">Log Response</button>
      </div>
    </aside>
  );
}
