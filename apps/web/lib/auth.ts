export type Session = {
  userId: string;
  email: string;
  token: string;
};

const SESSION_KEY = 'skripts.session';

export function getSession(): Session | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function requireSession(): Session {
  const session = getSession();
  if (!session) {
    throw new Error('NO_SESSION');
  }
  return session;
}

export function login(email: string, password: string): Session {
  if (!email.trim() || !password.trim()) {
    throw new Error('INVALID_CREDENTIALS');
  }

  const session: Session = {
    userId: 'user-1',
    email,
    token: crypto.randomUUID(),
  };

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  }

  return session;
}

export function logout(): void {
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(SESSION_KEY);
  }
}
