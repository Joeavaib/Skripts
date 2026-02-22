export const AUTH_TOKEN_KEY = 'skripts.auth.token';

export type AuthSession = {
  token: string;
  userId?: string;
  expiresAt?: string;
};

const isBrowser = typeof window !== 'undefined';

export function getStoredSession(): AuthSession | null {
  if (!isBrowser) return null;

  const token = window.localStorage.getItem(AUTH_TOKEN_KEY);
  if (!token) return null;

  const expiresAt = window.localStorage.getItem(`${AUTH_TOKEN_KEY}.expiresAt`) ?? undefined;
  const userId = window.localStorage.getItem(`${AUTH_TOKEN_KEY}.userId`) ?? undefined;

  return { token, expiresAt, userId };
}

export function storeSession(session: AuthSession): void {
  if (!isBrowser) return;

  window.localStorage.setItem(AUTH_TOKEN_KEY, session.token);
  if (session.expiresAt) {
    window.localStorage.setItem(`${AUTH_TOKEN_KEY}.expiresAt`, session.expiresAt);
  }
  if (session.userId) {
    window.localStorage.setItem(`${AUTH_TOKEN_KEY}.userId`, session.userId);
  }
}

export function clearSession(): void {
  if (!isBrowser) return;

  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  window.localStorage.removeItem(`${AUTH_TOKEN_KEY}.expiresAt`);
  window.localStorage.removeItem(`${AUTH_TOKEN_KEY}.userId`);
}

export function getAuthHeaders(additional?: HeadersInit): HeadersInit {
  const session = getStoredSession();

  return {
    ...(additional ?? {}),
    ...(session?.token ? { Authorization: `Bearer ${session.token}` } : {}),
  };
}

export async function withAuthRecovery<T>(request: () => Promise<T>): Promise<T> {
  try {
    return await request();
  } catch (error) {
    const status = (error as { status?: number }).status;
    if (status === 401) {
      clearSession();
      if (isBrowser) {
        window.location.assign('/login');
      }
    }
    throw error;
  }
}
