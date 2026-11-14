import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/lib/auth/AuthContext';

export const metadata: Metadata = {
  title: 'Clinical Ledger Precision — 통합 업무 포털',
  description: '병원부 미결 통합 관리 및 업무 테마별 포털 공간',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-[#faf8ff] text-[#131b2e] antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
