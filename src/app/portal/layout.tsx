'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/AuthContext';
import { THEME_MENU_GROUPS, MenuGroup } from '@/config/menuConfig';
import {
  Calculator,
  PieChart,
  BookOpen,
  PlusCircle,
  Building2,
  LogOut,
  LayoutDashboard,
  ChevronRight,
  ShieldAlert,
  User,
  ExternalLink,
  Code2,
  Menu,
  X,
  FileText
} from 'lucide-react';

const iconMap = {
  Calculator,
  PieChart,
  BookOpen,
  PlusCircle,
  User,
};

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading, logout, isSupabaseConnected, switchRole } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // 현재 URL 경로를 기반으로 활성 테마 감지
  const [activeThemeId, setActiveThemeId] = useState<string>(() => {
    if (pathname.includes('/finance')) return 'finance';
    if (pathname.includes('/tools')) return 'tools';
    if (pathname.includes('/blog') || pathname.includes('/profile')) return 'knowledge';
    if (pathname.includes('/new-menu-demo')) return 'extensible-demo';
    return 'finance';
  });

  useEffect(() => {
    if (pathname.includes('/finance')) setActiveThemeId('finance');
    else if (pathname.includes('/tools')) setActiveThemeId('tools');
    else if (pathname.includes('/blog') || pathname.includes('/profile')) setActiveThemeId('knowledge');
    else if (pathname.includes('/new-menu-demo')) setActiveThemeId('extensible-demo');
  }, [pathname]);

  // 비로그인 상태 가드
  useEffect(() => {
    if (!loading && !user) {
      router.replace('/login');
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#faf8ff]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-9 h-9 border-3 border-[#1e3a8a] border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs text-[#444651]">인증 세션을 확인하는 중...</span>
        </div>
      </div>
    );
  }

  const currentTheme = THEME_MENU_GROUPS.find((g) => g.themeId === activeThemeId) || THEME_MENU_GROUPS[0];

  return (
    <div className="min-h-screen bg-[#faf8ff] flex flex-col text-[#131b2e]">
      {/* ── GNB (Top Global Navigation Bar) ── */}
      <header className="sticky top-0 z-40 bg-[#00236f] text-white border-b border-[#1e3a8a] shadow-sm">
        <div className="max-w-[1720px] mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          {/* Brand Logo & Title */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-1.5 text-white/80 hover:text-white"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>

            <Link href="/portal" className="flex items-center gap-2.5">
              <span className="bg-[#1e3a8a] border border-[#3b82f6]/40 text-[#90a8ff] px-2 py-0.5 rounded text-[11px] font-headline font-bold tracking-wider">
                CLP
              </span>
              <span className="font-headline font-bold text-sm tracking-tight hidden sm:inline">
                Clinical Ledger Precision
              </span>
              <span className="text-[11px] text-[#dae2fd] hidden md:inline border-l border-white/20 pl-2.5">
                업무 통합 포털
              </span>
            </Link>
          </div>

          {/* Theme Switcher Tabs (Desktop GNB) */}
          <nav className="hidden lg:flex items-center gap-1">
            {THEME_MENU_GROUPS.map((group) => {
              const Icon = iconMap[group.iconName] || Calculator;
              const isActive = activeThemeId === group.themeId;
              return (
                <button
                  key={group.themeId}
                  onClick={() => {
                    setActiveThemeId(group.themeId);
                    router.push(group.dashboard.path);
                  }}
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition cursor-pointer ${
                    isActive
                      ? 'bg-[#1e3a8a] text-white shadow-inner border border-[#3b82f6]/50'
                      : 'text-white/80 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{group.themeTitle}</span>
                </button>
              );
            })}
          </nav>

          {/* User Profile & Actions */}
          <div className="flex items-center gap-3">
            {/* Supabase status indicator */}
            <div className="hidden xl:flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded bg-[#1e3a8a]/60 border border-[#3b82f6]/30 text-[#dae2fd]">
              <span className={`w-1.5 h-1.5 rounded-full ${isSupabaseConnected ? 'bg-[#10b981]' : 'bg-[#60a5fa]'}`} />
              <span>{isSupabaseConnected ? 'Supabase' : 'Demo DB'}</span>
            </div>

            {/* Role Switcher (for instant testing) */}
            <div className="hidden sm:flex items-center gap-1 bg-[#131b2e] px-2 py-1 rounded border border-white/10 text-[11px]">
              <span className="text-white/60">권한:</span>
              <select
                value={user.role}
                onChange={(e) => switchRole(e.target.value as any)}
                className="bg-transparent text-[#90a8ff] font-semibold focus:outline-none cursor-pointer"
              >
                <option value="finance_manager" className="bg-[#131b2e] text-white">Finance Manager</option>
                <option value="admin" className="bg-[#131b2e] text-white">Admin</option>
                <option value="staff" className="bg-[#131b2e] text-white">Staff</option>
              </select>
            </div>

            {/* User Info */}
            <div className="flex items-center gap-2 pl-2 border-l border-white/15">
              <div className="w-7 h-7 rounded-full bg-[#1e3a8a] border border-[#90a8ff]/40 flex items-center justify-center font-bold text-xs text-white">
                {user.name.charAt(0)}
              </div>
              <div className="hidden md:block text-left">
                <div className="text-xs font-semibold leading-tight">{user.name}</div>
                <div className="text-[10px] text-[#dae2fd]/70 leading-tight">{user.department}</div>
              </div>

              <button
                onClick={() => logout()}
                title="로그아웃"
                className="p-1.5 rounded text-white/70 hover:text-white hover:bg-white/10 transition ml-1"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Theme Switcher Bar */}
        <div className="lg:hidden flex overflow-x-auto px-4 py-2 gap-1.5 bg-[#001b57] border-t border-white/10">
          {THEME_MENU_GROUPS.map((group) => {
            const Icon = iconMap[group.iconName] || Calculator;
            const isActive = activeThemeId === group.themeId;
            return (
              <button
                key={group.themeId}
                onClick={() => {
                  setActiveThemeId(group.themeId);
                  router.push(group.dashboard.path);
                  setMobileMenuOpen(false);
                }}
                className={`shrink-0 flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold ${
                  isActive ? 'bg-[#1e3a8a] text-white' : 'text-white/70 hover:text-white'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{group.themeTitle}</span>
              </button>
            );
          })}
        </div>
      </header>

      {/* ── Main Workspace Body ── */}
      <div className="max-w-[1720px] w-full mx-auto flex-1 flex">
        {/* ── LNB (Sidebar Navigation) ── */}
        <aside
          className={`w-64 shrink-0 bg-white border-r border-[#e2e8f0] flex flex-col justify-between ${
            mobileMenuOpen ? 'fixed inset-y-0 left-0 z-50 pt-16 shadow-xl' : 'hidden lg:flex'
          }`}
        >
          <div className="p-4 space-y-5 overflow-y-auto">
            {/* Current Theme Header Card */}
            <div className="p-3 rounded-lg bg-[#f2f3ff] border border-[#dae2fd]">
              <div className="text-[11px] font-semibold text-[#1e3a8a] uppercase tracking-wider">
                선택된 업무 테마
              </div>
              <div className="text-sm font-bold text-[#00236f] mt-0.5">
                {currentTheme.themeTitle}
              </div>
              <p className="text-[11px] text-[#444651] mt-1 leading-snug">
                {currentTheme.themeDescription}
              </p>
            </div>

            {/* Dashboard Link (Always at top of theme) */}
            <div>
              <div className="text-[11px] font-semibold text-[#757682] px-2 mb-1.5 uppercase tracking-wider">
                메인 대시보드
              </div>
              <Link
                href={currentTheme.dashboard.path}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-semibold transition ${
                  pathname === currentTheme.dashboard.path
                    ? 'bg-[#1e3a8a] text-white shadow-sm'
                    : 'text-[#131b2e] hover:bg-[#eaedff] text-slate-700'
                }`}
              >
                <LayoutDashboard className="w-4 h-4 shrink-0" />
                <span className="truncate">{currentTheme.dashboard.title}</span>
              </Link>
            </div>

            {/* Submenus Group (신규 코딩 하위메뉴 그룹) */}
            <div>
              <div className="flex items-center justify-between text-[11px] font-semibold text-[#757682] px-2 mb-1.5 uppercase tracking-wider">
                <span>하위 세부메뉴 ({currentTheme.subMenus.length})</span>
                <span className="text-[10px] text-[#2563eb] font-normal">신규코딩 그룹</span>
              </div>

              <div className="space-y-1">
                {currentTheme.subMenus.map((sub) => {
                  const isActive = pathname === sub.path;
                  const hasPermission =
                    !sub.requiredRole || sub.requiredRole.includes(user.role);

                  if (!hasPermission) {
                    return (
                      <div
                        key={sub.id}
                        title={`접근 제한: ${sub.requiredRole?.join(', ')} 권한 필요`}
                        className="flex items-center justify-between px-3 py-2 rounded-md text-xs text-[#94a3b8] bg-[#f8fafc] cursor-not-allowed border border-dashed border-[#e2e8f0]"
                      >
                        <div className="flex items-center gap-2 truncate">
                          <ShieldAlert className="w-3.5 h-3.5 text-[#dc2626] shrink-0" />
                          <span className="truncate">{sub.title}</span>
                        </div>
                        <span className="text-[10px] px-1.5 py-0.2 bg-[#f1f5f9] text-[#64748b] rounded">
                          잠김
                        </span>
                      </div>
                    );
                  }

                  return (
                    <Link
                      key={sub.id}
                      href={sub.path}
                      className={`flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition ${
                        isActive
                          ? 'bg-[#00236f] text-white font-semibold shadow-sm'
                          : 'text-[#334155] hover:bg-[#eaedff] hover:text-[#00236f]'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <FileText className="w-3.5 h-3.5 shrink-0 opacity-70" />
                        <span className="truncate">{sub.title}</span>
                      </div>
                      {sub.badge && (
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded font-semibold shrink-0 ml-1.5 ${
                            sub.badgeType === 'new'
                              ? 'bg-[#eff6ff] text-[#2563eb] border border-[#bfdbfe]'
                              : sub.badgeType === 'settled'
                              ? 'bg-[#ecfdf5] text-[#059669] border border-[#a7f3d0]'
                              : sub.badgeType === 'critical'
                              ? 'bg-[#fef2f2] text-[#dc2626] border border-[#fecaca]'
                              : 'bg-[#fffbeb] text-[#d97706] border border-[#fde68a]'
                          }`}
                        >
                          {sub.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Sidebar Footer: Developer Extension Guide */}
          <div className="p-3 border-t border-[#e2e8f0] bg-[#faf8ff]">
            <Link
              href="/portal/new-menu-demo"
              className="flex items-center gap-2 p-2 rounded-md border border-[#cbd5e1] bg-white hover:bg-[#eaedff] transition text-[11px] text-[#1e3a8a] font-semibold"
            >
              <Code2 className="w-4 h-4 shrink-0 text-[#2563eb]" />
              <div className="leading-tight">
                <div>신규 메뉴 추가 가이드</div>
                <div className="text-[10px] text-[#757682] font-normal">menuConfig.ts 등록 방식</div>
              </div>
            </Link>
          </div>
        </aside>

        {/* ── Main Content Area ── */}
        <main className="flex-1 flex flex-col min-w-0 bg-[#faf8ff] p-4 sm:p-6 lg:p-8 overflow-y-auto">
          {/* Breadcrumb Header */}
          <div className="flex items-center gap-1.5 text-xs text-[#757682] mb-4">
            <Link href="/portal" className="hover:text-[#00236f] transition">포털 홈</Link>
            <ChevronRight className="w-3.5 h-3.5" />
            <span className="font-semibold text-[#1e3a8a]">{currentTheme.themeTitle}</span>
          </div>

          {/* Children Viewport */}
          <div className="flex-1">{children}</div>
        </main>
      </div>
    </div>
  );
}
