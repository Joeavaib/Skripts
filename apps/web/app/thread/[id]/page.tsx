'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ActionCards } from '../../../components/ActionCards';
import { ConfirmUndoBar } from '../../../components/ConfirmUndoBar';
import { actOnThread, getThreadDetail, type ActionCard, type ThreadDetail } from '../../../lib/api';

type Props = {
  params: {
    id: string;
  };
};

export default function ThreadDetailPage({ params }: Props) {
  const [thread, setThread] = useState<ThreadDetail | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    void getThreadDetail(params.id).then((value) => {
      if (active) setThread(value);
    });
    return () => {
      active = false;
    };
  }, [params.id]);

  const runAction = async (action: ActionCard['action']) => {
    if (!thread) return;
    setBusy(true);
    try {
      const result = await actOnThread(thread.id, action);
      setThread(result.thread);
    } finally {
      setBusy(false);
    }
  };

  if (!thread) return <p>Loading thread…</p>;

  return (
    <article style={{ display: 'grid', gap: 14 }}>
      <Link href={`/${thread.view}`}>← Back to {thread.view}</Link>
      <h1>{thread.title}</h1>
      <p>{thread.content}</p>

      <section>
        <h2>Action Cards</h2>
        <ActionCards cards={thread.cards} onRun={(action) => void runAction(action)} disabled={busy} />
      </section>

      <section>
        <h2>Confirm / Undo</h2>
        <ConfirmUndoBar onConfirm={() => void runAction('confirm')} onUndo={() => void runAction('undo')} busy={busy} />
      </section>
    </article>
  );
}
