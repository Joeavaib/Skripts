import Link from 'next/link';
import type { ReactNode } from 'react';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: 'system-ui, sans-serif', margin: 0, background: '#f8fafc' }}>
        <header style={{ borderBottom: '1px solid #e2e8f0', padding: '12px 20px', background: '#fff' }}>
          <nav style={{ display: 'flex', gap: 12 }}>
            <Link href="/unchecked">Unchecked</Link>
            <Link href="/now">Now</Link>
            <Link href="/later">Later</Link>
            <Link href="/done">Done</Link>
          </nav>
        </header>
        <main style={{ margin: '0 auto', maxWidth: 880, padding: 20 }}>{children}</main>
      </body>
    </html>
  );
}
