'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, BarChart3, TrendingUp, CheckCircle, Sparkles } from 'lucide-react';

export default function DemoAnalyticsSubMenuPage() {
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
          <div className="flex items-center gap-2 text-xs font-semibold text-[#1e3a8a] mb-1">
            <Sparkles className="w-4 h-4 text-[#2563eb]" />
            <span>신규 코딩 하위메뉴 템플릿</span>
          </div>
          <h1 className="text-xl font-bold font-headline text-[#00236f] tracking-tight">
            데이터 분석 서브메뉴 (Analytics Sub-View)
          </h1>
          <p className="text-xs text-[#757682] mt-1">
            신규 개발자가 컴포넌트를 자유롭게 추가하여 비즈니스 로직을 구현하는 표준 화면입니다.
          </p>
        </div>

        <span className="text-xs px-2.5 py-1 rounded bg-[#eff6ff] text-[#2563eb] font-bold border border-[#bfdbfe]">
          Submenu 01
        </span>
      </div>

      <div className="bg-white rounded-xl border border-[#cbd5e1] p-6 shadow-stitch-card">
        <h2 className="text-sm font-bold font-headline text-[#00236f] mb-3">
          샘플 분석 위젯
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-[#faf8ff] border border-[#e2e8f0]">
            <div className="text-xs text-[#757682] font-semibold">이번 달 데이터 처리량</div>
            <div className="text-xl font-bold font-mono text-[#00236f] mt-1 num-font">
              128,492 건
            </div>
            <div className="text-[11px] text-[#059669] mt-1">✓ 무결성 검증 100% 통과</div>
          </div>

          <div className="p-4 rounded-lg bg-[#faf8ff] border border-[#e2e8f0]">
            <div className="text-xs text-[#757682] font-semibold">평균 대사 소요 시간</div>
            <div className="text-xl font-bold font-mono text-[#1e3a8a] mt-1 num-font">
              0.42 초 / 건
            </div>
            <div className="text-[11px] text-[#2563eb] mt-1">Pyodide WASM 가속 적용</div>
          </div>
        </div>
      </div>
    </div>
  );
}
