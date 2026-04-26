import type { Pitch } from "../types";

export function TargetCard({ pitch, onOpen }: { pitch: Pitch; onOpen: () => void }) {
  return (
    <button onClick={onOpen} className="w-full rounded-lg border border-slate-700 bg-slate-900 p-3 text-left">
      <div className="mb-1 flex items-center justify-between">
        <span className="font-medium text-white">{pitch.venue_name}</span>
        <span className="text-xs uppercase text-slate-300">{pitch.status}</span>
      </div>
      <p className="text-xs text-slate-400">{pitch.pitch_subject}</p>
    </button>
  );
}
