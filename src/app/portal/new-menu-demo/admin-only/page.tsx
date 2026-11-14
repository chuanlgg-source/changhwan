'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth/AuthContext';
import { ArrowLeft, ShieldAlert, ShieldCheck, UserCheck } from 'lucide-react';

export default function AdminOnlySubMenuPage() {
  const { user, switchRole } = useAuth();
  const isAdmin = user?.role === 'admin';

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/portal/new-menu-demo"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#1e3a8a] hover:underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>가이드 대시보드로 돌아가기</span>
        </Link>
      </div>

      <div className="bg-white rounded-xl border border-[#cbd5e1] p-6 shadow-stitch-card flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#dc2626] mb-1">
            <ShieldAlert className="w-4 h-4" />
            <span>ROLE-BASED ACCESS CONTROL (RBAC)</span>
          </div>
          <h1 className="text-xl font-bold font-headline text-[#00236f] tracking-tight">
            관리자 전용 콘솔 하위메뉴
          </h1>
          <p className="text-xs text-[#757682] mt-1">
            `requiredRole: [&apos;admin&apos;]` 설정에 의해 Admin 권한 보유자에게만 활성화되는 메뉴입니다.
          </p>
        </div>

        <span className="text-xs px-2.5 py-1 rounded bg-[#fef2f2] text-[#dc2626] font-bold border border-[#fecaca]">
          Admin Only
        </span>
      </div>

      {!isAdmin ? (
        <div className="bg-white rounded-xl border border-[#fecaca] p-6 shadow-stitch-card bg-[#fff5f5]">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-6 h-6 text-[#dc2626] shrink-0" />
            <div>
              <h2 className="text-sm font-bold text-[#dc2626]">
                현재 접속 계정에는 접근 권한이 없습니다.
              </h2>
              <p className="text-xs text-[#757682] mt-1">
                현재 권한: <strong className="text-[#131b2e]">{user?.role}</strong> (Admin 권한 필요)
              </p>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-[#fecaca] flex items-center justify-between">
            <span className="text-xs text-[#444651]">
              상단 GNB의 권한 스위처 또는 아래 버튼을 눌러 즉시 Admin 권한으로 전환해보세요:
            </span>
            <button
              onClick={() => switchRole('admin')}
              className="px-3.5 py-1.5 bg-[#dc2626] text-white text-xs font-bold rounded-md hover:bg-[#b91c1c] transition flex items-center gap-1.5"
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>Admin 권한으로 즉시 전환</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-[#cbd5e1] p-6 shadow-stitch-card space-y-4">
          <div className="flex items-center gap-2 text-xs font-bold text-[#059669]">
            <ShieldCheck className="w-4 h-4" />
            <span>관리자 권한 인증 성공</span>
          </div>
          <h2 className="text-sm font-bold font-headline text-[#00236f]">
            시스템 보안 및 전산 감사 관리
          </h2>
          <p className="text-xs text-[#444651] leading-relaxed">
            전체 사내 사용자의 테마별 메뉴 접근 로그, Supabase RLS 정책 적용 상태, 원장 수정 이력을 열람하고 통제할 수 있습니다.
          </p>
        </div>
      )}
    </div>
  );
}
