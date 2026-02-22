'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { actOnThread, type ThreadSummary } from '../lib/api';
import { ConfirmUndoBar } from './ConfirmUndoBar';
import { ThreadList } from './ThreadList';

type Props = {
  initialThreads: ThreadSummary[];
};

export function SessionFlow({ initialThreads }: Props) {
  const [threads, setThreads] = useState(initialThreads);
  const [index, setIndex] = useState(0);
  const [busy, setBusy] = useState(false);

  const selected = useMemo(() => threads[index], [threads, index]);

  const runAction = useCallback(
    async (action: 'confirm' | 'undo') => {
      if (!selected) return;
      setBusy(true);
      try {
        await actOnThread(selected.id, action);
        setThreads((current) => current.filter((item) => item.id !== selected.id));
        setIndex((current) => Math.max(0, Math.min(current, threads.length - 2)));
      } finally {
        setBusy(false);
      }
    },
    [selected, threads.length],
  );

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (busy || threads.length === 0) return;

      if (event.key === 'j') {
        event.preventDefault();
        setIndex((current) => Math.min(current + 1, threads.length - 1));
      }

      if (event.key === 'k') {
        event.preventDefault();
        setIndex((current) => Math.max(current - 1, 0));
      }

      if (event.key === 'Enter') {
        event.preventDefault();
        void runAction('confirm');
      }

      if (event.key.toLowerCase() === 'z') {
        event.preventDefault();
        void runAction('undo');
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [busy, runAction, threads.length]);

  if (threads.length === 0) {
    return <p>✅ Session complete. Unchecked inbox is empty.</p>;
  }

  return (
    <div style={{ display: 'grid', gap: 14 }}>
      <p>
        Keyboard-first session: <kbd>j</kbd>/<kbd>k</kbd> to move, <kbd>Enter</kbd> to confirm, <kbd>z</kbd> to
        undo.
      </p>
      <ThreadList items={threads} selectedId={selected?.id} />
      <ConfirmUndoBar onConfirm={() => void runAction('confirm')} onUndo={() => void runAction('undo')} busy={busy} />
    </div>
  );
}
