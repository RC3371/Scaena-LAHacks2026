interface OutreachConfirmModalProps {
  open: boolean;
  subject: string;
  body: string;
  onConfirm: () => void;
  onClose: () => void;
}

export function OutreachConfirmModal({ open, subject, body, onConfirm, onClose }: OutreachConfirmModalProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4">
      <div className="w-full max-w-xl rounded-xl bg-slate-900 p-4">
        <h4 className="mb-2 text-lg font-semibold text-white">Confirm Outreach</h4>
        <p className="mb-2 text-sm text-slate-300">{subject}</p>
        <pre className="mb-4 whitespace-pre-wrap rounded bg-slate-800 p-3 text-xs text-slate-200">{body}</pre>
        <div className="flex gap-2">
          <button onClick={onConfirm} className="rounded bg-emerald-600 px-3 py-2 text-sm text-white">Confirm & Send</button>
          <button onClick={onClose} className="rounded bg-slate-700 px-3 py-2 text-sm text-white">Edit First</button>
        </div>
      </div>
    </div>
  );
}
