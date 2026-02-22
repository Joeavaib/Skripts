'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '../../lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();

    try {
      login(email, password);
      router.push('/threads');
    } catch {
      setError('Ungültige Login-Daten.');
    }
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md items-center px-4">
      <form className="w-full rounded-xl border border-slate-200 p-6 shadow-sm" onSubmit={onSubmit}>
        <h1 className="text-2xl font-semibold">Login</h1>
        <p className="mt-1 text-sm text-slate-600">Melde dich an, um deine Threads zu bearbeiten.</p>

        <label className="mt-5 block text-sm font-medium">
          E-Mail
          <input
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label className="mt-3 block text-sm font-medium">
          Passwort
          <input
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>

        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

        <button className="mt-5 w-full rounded bg-slate-900 px-4 py-2 text-white">Einloggen</button>
      </form>
    </main>
  );
}
