'use client';

type ConfirmDialogProps = {
  open: boolean;
  title: string;
  description: string;
  onConfirm: () => void;
  onCancel: () => void;
};

export function ConfirmDialog({ open, title, description, onConfirm, onCancel }: ConfirmDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-xl">
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="mt-2 text-sm text-slate-600">{description}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button className="rounded border border-slate-300 px-3 py-1.5" onClick={onCancel}>
            Abbrechen
          </button>
          <button className="rounded bg-slate-900 px-3 py-1.5 text-white" onClick={onConfirm}>
            Bestätigen
          </button>
        </div>
      </div>
    </div>
  );
}
