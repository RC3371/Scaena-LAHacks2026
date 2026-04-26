import type { Entertainer } from "../types";

export function EntertainerProfile({ entertainer }: { entertainer?: Entertainer }) {
  if (!entertainer) return null;
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
      <h3 className="text-white">{entertainer.name}</h3>
      <p className="text-sm text-slate-300">
        {entertainer.type} {entertainer.genre ? `· ${entertainer.genre}` : ""} {entertainer.location ? `· ${entertainer.location}` : ""}
      </p>
      <p className="mt-1 text-xs text-slate-400">Mode: {entertainer.outreach_mode}</p>
    </div>
  );
}
