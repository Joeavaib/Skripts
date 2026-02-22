'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { listThreads, ThreadSummary } from '../../lib/api';
import { getSession, logout } from '../../lib/auth';
import { useRouter } from 'next/navigation';

export default function ThreadListPage() {
  const router = useRouter();
  const [threads, setThreads] = useState<ThreadSummary[]>([]);

  useEffect(() => {
    const session = getSession();
    if (!session) {
      router.replace('/login');
      return;
    }

    listThreads().then(setThreads);
  }, [router]);

  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <header className="mb-5 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Threadliste</h1>
        <button
          className="rounded border border-slate-300 px-3 py-1.5 text-sm"
          onClick={() => {
            logout();
            router.push('/login');
          }}
        >
          Logout
        </button>
      </header>

      <ul className="space-y-3">
        {threads.map((thread) => (
          <li key={thread.id} className="rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-medium">{thread.title}</h2>
                <p className="text-sm text-slate-600">Offen: {thread.openCards}</p>
              </div>
              <div className="flex gap-2">
                <Link className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white" href={`/threads/${thread.id}`}>
                  Detail
                </Link>
                <Link className="rounded border border-slate-300 px-3 py-1.5 text-sm" href={`/conversation/${thread.id}`}>
                  Conversation
                </Link>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
