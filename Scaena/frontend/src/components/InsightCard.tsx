export function InsightCard({
  venue,
  interest,
  worked,
  nextAction,
}: {
  venue: string;
  interest?: string;
  worked?: string;
  nextAction?: string;
}) {
  return (
    <div className="rounded border border-slate-700 bg-slate-900 p-3">
      <div className="mb-1 text-sm font-medium text-white">{venue}</div>
      <div className="mb-1 text-xs text-slate-400">Interest: {interest || "n/a"}</div>
      <p className="text-xs text-slate-300">{worked || "No insight yet."}</p>
      {nextAction ? <p className="mt-1 text-xs text-emerald-300">Next: {nextAction}</p> : null}
    </div>
  );
}
