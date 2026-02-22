export type Card = {
  id: string;
  title: string;
  why_1s: string;
  checked: boolean;
};

export type ThreadSummary = {
  id: string;
  title: string;
  openCards: number;
  updatedAt: string;
};

export type ThreadDetail = {
  id: string;
  title: string;
  cards: Card[];
};

const db: Record<string, ThreadDetail> = {
  't-1': {
    id: 't-1',
    title: 'Onboarding: Produktverständnis',
    cards: [
      {
        id: 'c-1',
        title: 'Was ist der Kernnutzen?',
        why_1s: 'Schneller Start für neue Nutzerinnen und Nutzer.',
        checked: false,
      },
      {
        id: 'c-2',
        title: 'Wo haken User zuerst?',
        why_1s: 'Reibung direkt am Einstieg senkt Conversion.',
        checked: false,
      },
    ],
  },
  't-2': {
    id: 't-2',
    title: 'Retention Review',
    cards: [
      {
        id: 'c-3',
        title: 'Welche Gewohnheit wollen wir aufbauen?',
        why_1s: 'Habit loops erhöhen Wiederkehr und LTV.',
        checked: false,
      },
    ],
  },
};

const latency = async () => new Promise((resolve) => setTimeout(resolve, 90));

export async function listThreads(): Promise<ThreadSummary[]> {
  await latency();

  return Object.values(db).map((thread) => ({
    id: thread.id,
    title: thread.title,
    openCards: thread.cards.filter((card) => !card.checked).length,
    updatedAt: new Date().toISOString(),
  }));
}

export async function getThread(threadId: string): Promise<ThreadDetail | null> {
  await latency();
  return db[threadId] ? structuredClone(db[threadId]) : null;
}

export async function getConversation(conversationId: string): Promise<ThreadDetail | null> {
  await latency();
  return getThread(conversationId);
}

export async function setCardChecked(threadId: string, cardId: string, checked: boolean): Promise<Card | null> {
  await latency();
  const thread = db[threadId];
  if (!thread) {
    return null;
  }

  const card = thread.cards.find((candidate) => candidate.id === cardId);
  if (!card) {
    return null;
  }

  card.checked = checked;
  return structuredClone(card);
}
