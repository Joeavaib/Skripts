'use client';

type Props = {
  onConfirm: () => void;
  onUndo: () => void;
  busy?: boolean;
};

export function ConfirmUndoBar({ onConfirm, onUndo, busy }: Props) {
  return (
    <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
      <button type="button" onClick={onConfirm} disabled={busy}>
        Confirm (Enter)
      </button>
      <button type="button" onClick={onUndo} disabled={busy}>
        Undo (Z)
      </button>
    </div>
  );
}
