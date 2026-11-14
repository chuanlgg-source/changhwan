'use client';

import React from 'react';
import Link from 'next/link';
import {
  Code2,
  PlusCircle,
  FileCode,
  Layers,
  CheckCircle2,
  ArrowRight,
  ShieldAlert,
  Sparkles
} from 'lucide-react';

export default function NewMenuDemoGuidePage() {
  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-xl border border-[#cbd5e1] p-6 shadow-stitch-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#1e3a8a] mb-1">
            <Code2 className="w-4 h-4" />
            <span>EXTENSIBILITY & MODULAR ARCHITECTURE</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold font-headline text-[#00236f] tracking-tight">
            신규 대시보드 및 하위메뉴 그룹화 추가 가이드
          </h1>
          <p className="text-xs text-[#444651] mt-1">
            신규 화면을 코딩한 후 기존 포털 코드를 수정할 필요 없이 레지스트리 설정만으로 자동 그룹화되는 구조입니다.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded bg-[#ecfdf5] text-[#059669] font-bold border border-[#a7f3d0]">
            ✓ 플러그앤플레이 지원
          </span>
        </div>
      </div>

      {/* Step by step interactive cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white rounded-xl border border-[#cbd5e1] p-5 shadow-stitch-card">
          <div className="w-8 h-8 rounded-lg bg-[#eff6ff] text-[#2563eb] font-bold text-xs flex items-center justify-center mb-3">
            01
          </div>
          <h3 className="font-bold text-sm text-[#00236f] mb-2 flex items-center gap-1.5">
            <FileCode className="w-4 h-4 text-[#1e3a8a]" />
            <span>신규 페이지 코딩</span>
          </h3>
          <p className="text-xs text-[#444651] leading-relaxed">
            `src/app/portal/[도메인]/page.tsx`에 일반 React 컴포넌트로 원하는 업무 화면이나 대시보드를 자유롭게 코딩합니다.
          </p>
          <div className="mt-3 bg-[#f8fafc] p-2 rounded text-[11px] font-mono text-[#00236f] border border-[#e2e8f0]">
            src/app/portal/logistics/page.tsx
          </div>
        </div>

        <div className="bg-white rounded-xl border border-[#cbd5e1] p-5 shadow-stitch-card">
          <div className="w-8 h-8 rounded-lg bg-[#eff6ff] text-[#2563eb] font-bold text-xs flex items-center justify-center mb-3">
            02
          </div>
          <h3 className="font-bold text-sm text-[#00236f] mb-2 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-[#1e3a8a]" />
            <span>메뉴 레지스트리 등록</span>
          </h3>
          <p className="text-xs text-[#444651] leading-relaxed">
            `src/config/menuConfig.ts`에 신규 테마 또는 기존 테마 하위의 `subMenus` 배열에 항목(경로, 제목, 권한) 1줄을 추가합니다.
          </p>
          <div className="mt-3 bg-[#f8fafc] p-2 rounded text-[11px] font-mono text-[#00236f] border border-[#e2e8f0]">
            subMenus: [&#123; title: &apos;물류현황&apos;, ... &#125;]
          </div>
        </div>

        <div className="bg-white rounded-xl border border-[#cbd5e1] p-5 shadow-stitch-card">
          <div className="w-8 h-8 rounded-lg bg-[#eff6ff] text-[#2563eb] font-bold text-xs flex items-center justify-center mb-3">
            03
          </div>
          <h3 className="font-bold text-sm text-[#00236f] mb-2 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-[#059669]" />
            <span>포털 자동 동기화</span>
          </h3>
          <p className="text-xs text-[#444651] leading-relaxed">
            상단 GNB 테마 탭, 좌측 사이드바 LNB 트리, 브레드크럼 및 권한별 접근 제어가 자동으로 일괄 생성됩니다.
          </p>
          <div className="mt-3 bg-[#ecfdf5] p-2 rounded text-[11px] font-semibold text-[#059669] border border-[#a7f3d0]">
            빌드/설정 자동 동기화 완료
          </div>
        </div>
      </div>

      {/* Actual Live Code Example Box */}
      <div className="bg-white rounded-xl border border-[#cbd5e1] shadow-stitch-card overflow-hidden">
        <div className="p-4 bg-[#f2f3ff] border-b border-[#cbd5e1] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-[#1e3a8a]" />
            <span className="text-xs font-bold text-[#00236f]">
              실제 menuConfig.ts 등록 코드 조각 (TypeScript)
            </span>
          </div>
          <span className="text-[11px] text-[#757682]">선언형 레지스트리</span>
        </div>

        <div className="p-4 bg-[#0f172a] text-[#dae2fd] font-mono text-xs overflow-x-auto leading-relaxed">
          <pre>{`// src/config/menuConfig.ts 에 추가하는 예시
{
  themeId: 'logistics',
  themeTitle: '물류/유통 관리',
  themeDescription: '의약품 배송 및 창고 재고 현황 모니터링',
  iconName: 'PlusCircle',
  dashboard: {
    id: 'logistics-dash',
    title: '물류 총괄 대시보드',
    path: '/portal/logistics/dashboard',
  },
  subMenus: [
    {
      id: 'stock-check',
      title: '창고 실시간 재고 대사',
      path: '/portal/logistics/stock',
      badge: '신규코딩',
      badgeType: 'new'
    },
    {
      id: 'restricted-menu',
      title: '물류 센터 관리자 콘솔',
      path: '/portal/logistics/admin',
      requiredRole: ['admin'], // ← 관리자만 접근 가능
      badge: 'Admin',
      badgeType: 'critical'
    }
  ]
}`}</pre>
        </div>
      </div>

      {/* Tested Submenus Preview Box */}
      <div className="bg-white rounded-xl border border-[#cbd5e1] p-6 shadow-stitch-card space-y-4">
        <h2 className="text-sm font-bold font-headline text-[#00236f]">
          현재 등록된 테스트 하위메뉴 바로가기
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link
            href="/portal/new-menu-demo/analytics"
            className="p-4 rounded-lg border border-[#e2e8f0] bg-[#faf8ff] hover:border-[#1e3a8a] transition flex items-center justify-between"
          >
            <div>
              <div className="text-xs font-bold text-[#00236f]">신규 하위메뉴 1: 데이터 분석 템플릿</div>
              <div className="text-[11px] text-[#757682] mt-0.5">신규 코딩하여 추가한 서브 뷰</div>
            </div>
            <ArrowRight className="w-4 h-4 text-[#1e3a8a]" />
          </Link>

          <Link
            href="/portal/new-menu-demo/admin-only"
            className="p-4 rounded-lg border border-[#e2e8f0] bg-[#faf8ff] hover:border-[#1e3a8a] transition flex items-center justify-between"
          >
            <div>
              <div className="text-xs font-bold text-[#00236f] flex items-center gap-1.5">
                <span>신규 하위메뉴 2: 관리자 전용 화면</span>
                <span className="text-[10px] px-1.5 py-0.2 bg-[#fef2f2] text-[#dc2626] rounded border border-[#fecaca]">Admin</span>
              </div>
              <div className="text-[11px] text-[#757682] mt-0.5">상단 권한을 Admin으로 변경 후 테스트</div>
            </div>
            <ArrowRight className="w-4 h-4 text-[#1e3a8a]" />
          </Link>
        </div>
      </div>
    </div>
  );
}
