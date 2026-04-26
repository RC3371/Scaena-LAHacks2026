import { useState } from "react";
import type { Venue } from "../types";

interface Agent1PanelProps {
  venues: Venue[];
  onRefine: (instruction: string) => Promise<void>;
}

export function Agent1Panel({ venues, onRefine }: Agent1PanelProps) {
  const [instruction, setInstruction] = useState("");
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
        <h3 className="mb-2 text-white">Research Refinement</h3>
        <textarea
          className="w-full rounded bg-slate-800 p-2 text-sm text-white"
          placeholder="Focus on outdoor festivals..."
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
        />
        <button onClick={() => onRefine(instruction)} className="mt-2 rounded bg-blue-600 px-3 py-2 text-sm text-white">Send to Agent 1</button>
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        {venues.map((v) => (
          <div key={v.id} className="rounded border border-slate-700 bg-slate-900 p-3">
            <div className="text-sm font-medium text-white">{v.name}</div>
            <div className="text-xs text-slate-400">{v.typical_pay}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
