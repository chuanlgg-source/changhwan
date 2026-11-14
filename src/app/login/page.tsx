'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/AuthContext';
import { ShieldCheck, Lock, Mail, ArrowRight, Sparkles, Building2, UserCheck } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login, isSupabaseConnected } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setErrorMsg('이메일을 입력해주세요.');
      return;
    }
    setSubmitting(true);
    setErrorMsg('');

    const res = await login(email, password);
    setSubmitting(false);

    if (res.success) {
      router.push('/portal');
    } else {
      setErrorMsg(res.error || '로그인에 실패했습니다. 계정 정보를 확인해주세요.');
    }
  };

  const handleQuickDemoLogin = async (demoEmail: string) => {
    setSubmitting(true);
    const res = await login(demoEmail, 'password123');
    setSubmitting(false);
    if (res.success) {
      router.push('/portal');
    }
  };

  return (
    <div className="min-h-screen bg-[#faf8ff] flex flex-col justify-center items-center p-4 sm:p-6">
      {/* Background ambient decoration */}
      <div className="absolute top-12 left-1/2 -translate-x-1/2 w-full max-w-4xl h-80 bg-gradient-to-b from-[#eaedff] to-transparent rounded-full blur-3xl pointer-events-none opacity-60"></div>

      <div className="w-full max-w-md relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#1e3a8a]/10 border border-[#1e3a8a]/20 text-[#1e3a8a] text-xs font-semibold tracking-wide mb-3">
            <Building2 className="w-3.5 h-3.5" />
            <span>CLINICAL LEDGER PRECISION</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold font-headline text-[#00236f] tracking-tight">
            업무 통합 포털 시스템
          </h1>
          <p className="text-xs sm:text-sm text-[#444651] mt-1.5">
            병원부 미결 관리, 재무 분석, 지식 공유 통합 워크스페이스
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-xl border border-[#cbd5e1] shadow-stitch-elevated p-6 sm:p-8">
          {/* Supabase Status Banner */}
          <div className="mb-6 p-3 rounded-lg border text-xs flex items-center justify-between gap-2 bg-[#f2f3ff] border-[#dae2fd]">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${isSupabaseConnected ? 'bg-[#059669]' : 'bg-[#2563eb] animate-pulse'}`}></span>
              <span className="font-medium text-[#131b2e]">
                {isSupabaseConnected ? 'Supabase 클라우드 연동 활성화' : '로컬 데모 & 목업 모드 동작 중'}
              </span>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded bg-white text-[#1e3a8a] font-semibold border border-[#c5c5d3]">
              {isSupabaseConnected ? 'Supabase Auth' : 'Demo Auth'}
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#131b2e] mb-1">
                업무용 이메일
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#757682] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@hospital.com"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-[#faf8ff] border border-[#cbd5e1] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1e3a8a] focus:bg-white text-[#131b2e] transition"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#131b2e] mb-1">
                비밀번호
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#757682] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-[#faf8ff] border border-[#cbd5e1] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1e3a8a] focus:bg-white text-[#131b2e] transition"
                />
              </div>
            </div>

            {errorMsg && (
              <div className="p-2.5 rounded bg-[#fef2f2] border border-[#fecaca] text-[#dc2626] text-xs flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 px-4 bg-[#00236f] hover:bg-[#1e3a8a] active:bg-[#00174c] text-white text-xs font-semibold rounded-md shadow transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60"
            >
              {submitting ? '인증 처리 중...' : '포털 시스템 로그인'}
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          {/* Quick Demo Logins */}
          <div className="mt-6 pt-5 border-t border-[#e2e8f0]">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-[#444651] mb-2.5">
              <Sparkles className="w-3.5 h-3.5 text-[#1e3a8a]" />
              <span>원클릭 빠른 테스트 계정</span>
            </div>
            <div className="grid grid-cols-1 gap-2">
              <button
                type="button"
                onClick={() => handleQuickDemoLogin('chuan@hospital.com')}
                className="w-full text-left p-2 rounded-md border border-[#cbd5e1] bg-[#faf8ff] hover:bg-[#eaedff] transition flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-[#00236f] flex items-center gap-1.5">
                    <UserCheck className="w-3.5 h-3.5 text-[#059669]" />
                    <span>이창환 (정산 총괄 매니저)</span>
                  </div>
                  <div className="text-[11px] text-[#757682]">chuan@hospital.com • 병원사업부</div>
                </div>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[#ecfdf5] text-[#059669] border border-[#a7f3d0]">
                  Finance Manager
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickDemoLogin('admin@hospital.com')}
                className="w-full text-left p-2 rounded-md border border-[#cbd5e1] bg-[#faf8ff] hover:bg-[#eaedff] transition flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-[#00236f] flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#2563eb]" />
                    <span>시스템 관리자</span>
                  </div>
                  <div className="text-[11px] text-[#757682]">admin@hospital.com • IT인프라팀</div>
                </div>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[#eff6ff] text-[#2563eb] border border-[#bfdbfe]">
                  Admin
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="text-center mt-6 text-xs text-[#757682]">
          © 2026 Clinical Ledger Precision. All rights reserved.
        </div>
      </div>
    </div>
  );
}
