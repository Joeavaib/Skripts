'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, getThread, setCardChecked, ThreadDetail } from '../../../lib/api';
import { getSession } from '../../../lib/auth';
import { CardItem } from '../../components/CardItem';
import { ConfirmDialog } from '../../components/ConfirmDialog';

type UndoState = {
  card: Card;
  expiresAt: number;
} | null;

export default function ThreadDetailPage() {
  const params = useParams<{ threadId: string }>();
  const router = useRouter();
  const [thread, setThread] = useState<ThreadDetail | null>(null);
  const [focusIndex, setFocusIndex] = useState(0);
  const [pendingCard, setPendingCard] = useState<Card | null>(null);
  const [undoState, setUndoState] = useState<UndoState>(null);

  useEffect(() => {
    const session = getSession();
    if (!session) {
      router.replace('/login');
      return;
    }

    getThread(params.threadId).then(setThread);
  }, [params.threadId, router]);

  const uncheckedCards = useMemo(
    () => thread?.cards.filter((card) => !card.checked) ?? [],
    [thread],
  );

  useEffect(() => {
    if (focusIndex >= uncheckedCards.length) {
      setFocusIndex(Math.max(uncheckedCards.length - 1, 0));
    }
  }, [focusIndex, uncheckedCards.length]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (!thread || uncheckedCards.length === 0) {
        return;
      }

      if (event.key === 'j') {
        event.preventDefault();
        setFocusIndex((current) => Math.min(current + 1, uncheckedCards.length - 1));
      }

      if (event.key === 'k') {
        event.preventDefault();
        setFocusIndex((current) => Math.max(current - 1, 0));
      }

      if (event.key === 'Enter') {
        event.preventDefault();
        setPendingCard(uncheckedCards[focusIndex]);
      }

      if (event.key === 'u' && undoState) {
        event.preventDefault();
        undoCheck();
      }
    };

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  const confirmCheck = async () => {
    if (!thread || !pendingCard) {
      return;
    }

    const updated = await setCardChecked(thread.id, pendingCard.id, true);
    if (!updated) {
      setPendingCard(null);
      return;
    }

    setThread((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        cards: current.cards.map((card) => (card.id === updated.id ? updated : card)),
      };
    });

    setUndoState({ card: pendingCard, expiresAt: Date.now() + 5000 });
    setPendingCard(null);
  };

  const undoCheck = async () => {
    if (!thread || !undoState) {
      return;
    }

    const updated = await setCardChecked(thread.id, undoState.card.id, false);
    if (!updated) {
      return;
    }

    setThread((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        cards: current.cards.map((card) => (card.id === updated.id ? updated : card)),
      };
    });

    setUndoState(null);
  };

  useEffect(() => {
    if (!undoState) {
      return;
    }

    const timer = window.setTimeout(() => setUndoState(null), Math.max(undoState.expiresAt - Date.now(), 0));
    return () => window.clearTimeout(timer);
  }, [undoState]);

  if (!thread) {
    return <main className="p-6">Lade Thread…</main>;
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-2xl font-semibold">{thread.title}</h1>
      <p className="mt-1 text-sm text-slate-600">
        Session-Flow: unchecked until empty ({uncheckedCards.length} offen) · Tasten: j/k navigieren, Enter checken, u undo.
      </p>

      {undoState ? (
        <div className="mt-4 flex items-center justify-between rounded border border-amber-300 bg-amber-50 p-3 text-sm">
          <span>Card als erledigt markiert.</span>
          <button className="rounded border border-amber-400 px-2 py-1" onClick={undoCheck}>
            Undo (u)
          </button>
        </div>
      ) : null}

      {uncheckedCards.length === 0 ? (
        <div className="mt-6 rounded-lg border border-emerald-300 bg-emerald-50 p-4">Alles erledigt ✅</div>
      ) : (
        <section className="mt-6 space-y-3">
          {uncheckedCards.map((card, index) => (
            <CardItem key={card.id} card={card} focused={index === focusIndex} onCheck={() => setPendingCard(card)} />
          ))}
        </section>
      )}

      <ConfirmDialog
        open={Boolean(pendingCard)}
        title="Card als erledigt markieren?"
        description={pendingCard ? `„${pendingCard.title}“ wird aus der unchecked-Queue entfernt.` : ''}
        onCancel={() => setPendingCard(null)}
        onConfirm={confirmCheck}
      />
    </main>
  );
}
