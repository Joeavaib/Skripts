'use client';

import { Card } from '../../lib/api';

type CardItemProps = {
  card: Card;
  focused: boolean;
  onCheck: () => void;
};

export function CardItem({ card, focused, onCheck }: CardItemProps) {
  return (
    <article
      className={`rounded-lg border p-4 transition ${
        focused ? 'border-blue-500 ring-2 ring-blue-200' : 'border-slate-200'
      } ${card.checked ? 'opacity-60' : ''}`}
      aria-current={focused}
    >
      <header className="flex items-start justify-between gap-4">
        <h4 className="font-medium text-slate-900">{card.title}</h4>
        <button
          className="rounded bg-slate-100 px-2 py-1 text-xs hover:bg-slate-200"
          onClick={onCheck}
          disabled={card.checked}
        >
          {card.checked ? 'Erledigt' : 'Check'}
        </button>
      </header>
      <p className="mt-2 text-sm text-slate-600">why_1s: {card.why_1s}</p>
    </article>
  );
}
