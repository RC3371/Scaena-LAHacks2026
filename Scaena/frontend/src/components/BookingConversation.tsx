export function BookingConversation({
  messages,
  onMarkSent,
}: {
  messages: Array<{ id: string; stage: string; subject: string; body: string; status: string }>;
  onMarkSent: (id: string) => Promise<void>;
}) {
  return (
    <div className="space-y-2">
      {messages.map((m) => (
        <div key={m.id} className="rounded border border-slate-700 bg-slate-900 p-3">
          <div className="mb-1 text-xs uppercase text-slate-400">{m.stage}</div>
          <div className="text-sm text-white">{m.subject}</div>
          <p className="mt-1 text-xs text-slate-300">{m.body}</p>
          {m.status !== "sent" ? (
            <button onClick={() => onMarkSent(m.id)} className="mt-2 rounded bg-emerald-600 px-2 py-1 text-xs text-white">
              Mark Sent
            </button>
          ) : null}
        </div>
      ))}
    </div>
  );
}
