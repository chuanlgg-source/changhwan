-- ==============================================================================
-- Clinical Ledger Precision — Supabase Database Schema & Account Management
-- Project URL: https://cbarfruyknhfjvvhcmgu.supabase.co
-- ==============================================================================

-- 1. 포털 업무 계정 관리 테이블 (이메일/비밀번호/권한/부서/상태 통합 관리)
create table if not exists public.portal_users (
  id uuid default gen_random_uuid() primary key,
  email text unique not null,
  password_hash text not null, -- 초기/변경 비밀번호 (내부관리용)
  full_name text not null,
  department text default '병원사업부',
  role text default 'finance_manager' check (role in ('admin', 'finance_manager', 'staff')),
  status text default 'active' check (status in ('active', 'locked')),
  last_login timestamp with time zone,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.portal_users enable row level security;

create policy "포털 계정 조회 허용" on public.portal_users
  for select using (true);

create policy "포털 계정 추가/수정/삭제 허용" on public.portal_users
  for all using (true);

-- 기본 초기 관리자 및 총괄 매니저 계정 시드 데이터
insert into public.portal_users (email, password_hash, full_name, department, role, status)
values
  ('admin@hospital.com', 'admin1234', '시스템 관리자', 'IT 인프라팀 / 내부관리', 'admin', 'active'),
  ('chuan@hospital.com', 'password123', '이창환', '병원사업부 / 정산총괄', 'finance_manager', 'active'),
  ('staff@hospital.com', 'staff1234', '김정산 주임', '재무관리팀', 'staff', 'active')
on conflict (email) do nothing;


-- 2. 업무 지식 블로그 & 공지사항 테이블
create table if not exists public.blog_posts (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  slug text unique not null,
  category text default '공지' check (category in ('공지', '업무가이드', '정산리포트', '시스템개선')),
  author_name text not null default '관리자',
  author_role text default '정산 매니저',
  summary text,
  content text not null,
  tags text[] default array['병원부'],
  is_published boolean default true,
  view_count integer default 0,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.blog_posts enable row level security;

create policy "블로그 글 전체 조회 및 관리 허용" on public.blog_posts
  for all using (true);


-- 3. 포털 동적 메뉴 설정 저장 테이블
create table if not exists public.portal_menus (
  id text primary key default 'default_config',
  menu_json jsonb not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.portal_menus enable row level security;

create policy "메뉴 설정 조회 및 업데이트 허용" on public.portal_menus
  for all using (true);
