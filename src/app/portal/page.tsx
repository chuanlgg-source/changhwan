'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth/AuthContext';
import { THEME_MENU_GROUPS } from '@/config/menuConfig';
import {
  Calculator,
  PieChart,
  BookOpen,
  PlusCircle,
  ArrowRight,
  TrendingUp,
  FileCheck2,
  AlertCircle,
  Clock,
  Sparkles
} from 'lucide-react';
import { initialBlogPosts } from '@/lib/supabase/mockData';

const iconMap = {
  Calculator,
  PieChart,
  BookOpen,
  PlusCircle,
};

export default function PortalDashboardHomePage() {
  const { user } = useAuth();
  const recentPosts = initialBlogPosts.slice(0, 3);

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-[#00236f] via-[#1e3a8a] to-[#2563eb] rounded-xl text-white p-6 shadow-stitch-elevated flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-white/15 text-[#dae2fd] text-[11px] font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
            <span>Clinical Ledger Precision v2.4</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold font-headline tracking-tight">
            반갑습니다, {user?.name}님!
          </h1>
          <p className="text-xs sm:text-sm text-[#dae2fd] mt-1 max-w-2xl">
            업무 테마별로 통합된 대시보드와 서브메뉴를 통해 원장 대사, 금융 시뮬레이션 및 사내 지식 관리를 원스톱으로 수행하세요.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/portal/finance/dashboard"
            className="px-4 py-2 bg-white text-[#00236f] text-xs font-bold rounded-md hover:bg-[#eaedff] transition flex items-center gap-1.5 shadow"
          >
            <span>정산 대시보드 열기</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-[#cbd5e1] shadow-stitch-card">
          <div className="flex items-center justify-between text-xs text-[#757682] font-medium">
            <span>하반기 총 정산 예정금</span>
            <TrendingUp className="w-4 h-4 text-[#1e3a8a]" />
          </div>
          <div className="text-xl font-bold font-mono text-[#00236f] mt-1.5 num-font">
            ₩ 1,482,900,000
          </div>
          <div className="text-[11px] text-[#059669] font-medium mt-1 flex items-center gap-1">
            <span>↑ 전년 동기 대비 8.4% 증가</span>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-[#cbd5e1] shadow-stitch-card">
          <div className="flex items-center justify-between text-xs text-[#757682] font-medium">
            <span>집행 완료 (완결 건수)</span>
            <FileCheck2 className="w-4 h-4 text-[#059669]" />
          </div>
          <div className="text-xl font-bold font-mono text-[#059669] mt-1.5 num-font">
            324 <span className="text-xs font-normal text-[#444651]">/ 350 건</span>
          </div>
          <div className="text-[11px] text-[#757682] mt-1">
            정산 진척률 92.5% 달성
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-[#cbd5e1] shadow-stitch-card">
          <div className="flex items-center justify-between text-xs text-[#757682] font-medium">
            <span>미결 잔액 (대사 대기)</span>
            <AlertCircle className="w-4 h-4 text-[#dc2626]" />
          </div>
          <div className="text-xl font-bold font-mono text-[#dc2626] mt-1.5 num-font">
            ₩ 43,200,000
          </div>
          <div className="text-[11px] text-[#dc2626] font-medium mt-1">
            26건 미결 사유 입력 필요
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-[#cbd5e1] shadow-stitch-card">
          <div className="flex items-center justify-between text-xs text-[#757682] font-medium">
            <span>지식 허브 / 공지사항</span>
            <Clock className="w-4 h-4 text-[#2563eb]" />
          </div>
          <div className="text-xl font-bold font-mono text-[#1e3a8a] mt-1.5 num-font">
            {initialBlogPosts.length} <span className="text-xs font-normal text-[#444651]">건 등록됨</span>
          </div>
          <div className="text-[11px] text-[#2563eb] font-medium mt-1">
            최근 2일 전 새 글 업데이트
          </div>
        </div>
      </div>

      {/* Main Grid: Theme Workspace Navigation & Recent Blog Posts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Theme Groups */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold font-headline text-[#00236f] flex items-center gap-2">
              <span>업무 테마별 통합 공간 바로가기</span>
              <span className="text-xs font-normal text-[#757682]">({THEME_MENU_GROUPS.length}개 테마)</span>
            </h2>
            <Link
              href="/portal/new-menu-demo"
              className="text-xs text-[#2563eb] hover:underline flex items-center gap-1 font-semibold"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>신규 테마/메뉴 추가 방법</span>
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {THEME_MENU_GROUPS.map((group) => {
              const Icon = iconMap[group.iconName as keyof typeof iconMap] || Calculator;
              return (
                <div
                  key={group.themeId}
                  className="bg-white rounded-lg border border-[#cbd5e1] p-5 shadow-stitch-card hover:border-[#1e3a8a] hover:shadow-stitch-elevated transition flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div className="w-9 h-9 rounded-lg bg-[#eaedff] text-[#00236f] flex items-center justify-center">
                        <Icon className="w-5 h-5" />
                      </div>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[#f2f3ff] text-[#1e3a8a] border border-[#dae2fd]">
                        서브메뉴 {group.subMenus.length}개
                      </span>
                    </div>

                    <h3 className="font-bold text-sm text-[#00236f]">{group.themeTitle}</h3>
                    <p className="text-xs text-[#444651] mt-1 line-clamp-2">
                      {group.themeDescription}
                    </p>

                    {/* Submenu mini list */}
                    <div className="mt-4 pt-3 border-t border-[#f1f5f9] space-y-1.5">
                      <div className="text-[10px] font-semibold text-[#757682] uppercase">
                        포함된 기능 목록:
                      </div>
                      {group.subMenus.map((sub) => (
                        <Link
                          key={sub.id}
                          href={sub.path}
                          className="flex items-center justify-between text-xs text-[#334155] hover:text-[#00236f] hover:underline"
                        >
                          <span className="truncate">• {sub.title}</span>
                          {sub.badge && (
                            <span className="text-[9px] px-1 py-0.2 rounded bg-[#f1f5f9] text-[#475569]">
                              {sub.badge}
                            </span>
                          )}
                        </Link>
                      ))}
                    </div>
                  </div>

                  <div className="mt-5 pt-3 border-t border-[#e2e8f0]">
                    <Link
                      href={group.dashboard.path}
                      className="w-full py-1.5 px-3 bg-[#f2f3ff] hover:bg-[#1e3a8a] hover:text-white text-[#1e3a8a] text-xs font-semibold rounded flex items-center justify-center gap-1 transition"
                    >
                      <span>대시보드 이동</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Col: Knowledge & Blog Widget */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold font-headline text-[#00236f] flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-[#1e3a8a]" />
              <span>최신 업무 지식 & 공지</span>
            </h2>
            <Link
              href="/portal/blog"
              className="text-xs text-[#2563eb] hover:underline font-semibold"
            >
              전체보기
            </Link>
          </div>

          <div className="bg-white rounded-lg border border-[#cbd5e1] p-4 shadow-stitch-card space-y-3">
            {recentPosts.map((post) => (
              <Link
                key={post.id}
                href={`/portal/blog/${post.id}`}
                className="block p-3 rounded-md hover:bg-[#faf8ff] border border-transparent hover:border-[#dae2fd] transition"
              >
                <div className="flex items-center gap-2 text-[11px] mb-1">
                  <span className="px-1.5 py-0.2 rounded bg-[#eff6ff] text-[#2563eb] font-semibold border border-[#bfdbfe]">
                    {post.category}
                  </span>
                  <span className="text-[#757682]">{post.date}</span>
                </div>
                <h4 className="text-xs font-bold text-[#131b2e] hover:text-[#00236f] line-clamp-1">
                  {post.title}
                </h4>
                <p className="text-[11px] text-[#444651] mt-1 line-clamp-2">
                  {post.summary}
                </p>
              </Link>
            ))}

            <div className="pt-2 border-t border-[#f1f5f9]">
              <Link
                href="/portal/blog/write"
                className="w-full py-2 bg-[#00236f] hover:bg-[#1e3a8a] text-white text-xs font-semibold rounded flex items-center justify-center gap-1.5 transition"
              >
                <span>새 업무 글 작성하기</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
