'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { getConversation, ThreadDetail } from '../../../lib/api';

export default function ConversationPage() {
  const params = useParams<{ conversationId: string }>();
  const [conversation, setConversation] = useState<ThreadDetail | null>(null);

  useEffect(() => {
    getConversation(params.conversationId).then(setConversation);
  }, [params.conversationId]);

  if (!conversation) {
    return <main className="p-6">Lade Conversation…</main>;
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-2xl font-semibold">Conversation: {conversation.title}</h1>
      <p className="mt-1 text-sm text-slate-600">Kontextansicht der Cards inkl. why_1s.</p>

      <ul className="mt-6 space-y-3">
        {conversation.cards.map((card) => (
          <li key={card.id} className="rounded-lg border border-slate-200 p-4">
            <h2 className="font-medium">{card.title}</h2>
            <p className="mt-1 text-sm text-slate-600">why_1s: {card.why_1s}</p>
            <p className="mt-2 text-xs uppercase text-slate-500">Status: {card.checked ? 'checked' : 'unchecked'}</p>
          </li>
        ))}
      </ul>

      <Link href={`/threads/${conversation.id}`} className="mt-5 inline-block rounded border border-slate-300 px-3 py-1.5 text-sm">
        Zurück zum Thread
      </Link>
    </main>
  );
}
