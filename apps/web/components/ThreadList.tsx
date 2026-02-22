'use client';

import Link from 'next/link';
import type { ThreadSummary } from '../lib/api';

type Props = {
  items: ThreadSummary[];
  selectedId?: string;
};

export function ThreadList({ items, selectedId }: Props) {
  if (items.length === 0) {
    return <p>No threads left in this view.</p>;
  }

  return (
    <ul style={{ display: 'grid', gap: 10, listStyle: 'none', padding: 0 }}>
      {items.map((thread) => (
        <li key={thread.id}>
          <Link
            href={`/thread/${thread.id}`}
            style={{
              border: selectedId === thread.id ? '2px solid #0f766e' : '1px solid #d4d4d8',
              display: 'block',
              borderRadius: 8,
              padding: 12,
              textDecoration: 'none',
              color: 'inherit',
            }}
          >
            <strong>{thread.title}</strong>
            <p style={{ margin: '8px 0 0' }}>{thread.preview}</p>
          </Link>
        </li>
      ))}
    </ul>
  );
}
