import { getAuthHeaders, withAuthRecovery } from './auth';

export type ThreadView = 'unchecked' | 'now' | 'later' | 'done';

export type ActionCard = {
  id: string;
  title: string;
  description: string;
  action: 'confirm' | 'undo' | 'snooze-now' | 'snooze-later';
};

export type ThreadSummary = {
  id: string;
  title: string;
  preview: string;
  priority: 'low' | 'normal' | 'high';
  updatedAt: string;
  view: ThreadView;
};

export type ThreadDetail = ThreadSummary & {
  content: string;
  cards: ActionCard[];
  history: Array<{ id: string; label: string; at: string }>;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api';

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(init?.headers),
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    const error = new Error(`API request failed (${response.status})`) as Error & { status?: number };
    error.status = response.status;
    throw error;
  }

  return response.json() as Promise<T>;
}

export async function getViewThreads(view: ThreadView): Promise<ThreadSummary[]> {
  return withAuthRecovery(() => apiFetch<ThreadSummary[]>(`/threads?view=${view}`));
}

export async function getThreadDetail(id: string): Promise<ThreadDetail> {
  return withAuthRecovery(() => apiFetch<ThreadDetail>(`/threads/${id}`));
}

export async function actOnThread(
  id: string,
  action: ActionCard['action'],
): Promise<{ ok: true; thread: ThreadDetail }> {
  return withAuthRecovery(() =>
    apiFetch<{ ok: true; thread: ThreadDetail }>(`/threads/${id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    }),
  );
}
