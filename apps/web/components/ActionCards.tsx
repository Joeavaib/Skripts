'use client';

import type { ActionCard } from '../lib/api';

type Props = {
  cards: ActionCard[];
  onRun: (action: ActionCard['action']) => void;
  disabled?: boolean;
};

export function ActionCards({ cards, onRun, disabled }: Props) {
  return (
    <div style={{ display: 'grid', gap: 10 }}>
      {cards.map((card) => (
        <button
          key={card.id}
          type="button"
          disabled={disabled}
          onClick={() => onRun(card.action)}
          style={{
            textAlign: 'left',
            border: '1px solid #cbd5e1',
            borderRadius: 8,
            padding: 12,
            background: '#fff',
            cursor: disabled ? 'not-allowed' : 'pointer',
          }}
        >
          <strong>{card.title}</strong>
          <p style={{ margin: '6px 0 0' }}>{card.description}</p>
        </button>
      ))}
    </div>
  );
}
