-- ==============================================================================
-- Clinical Ledger Precision — Supabase Database Schema & RLS Setup
-- ==============================================================================

-- 1. 사용자 프로필 및 역할 관리 테이블 (Supabase Auth와 1:1 연동)
create table if not exists public.profiles (
  id uuid references auth.users on delete cascade primary key,
  email text not null,
  full_name text default '사용자',
  role text default 'staff' check (role in ('admin', 'finance_manager', 'staff')),
  department text default '병원사업부',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Profiles RLS 활성화
alter table public.profiles enable row level security;

create policy "프로필은 누구나 조회 가능" on public.profiles
  for select using (true);

create policy "본인 프로필만 수정 가능" on public.profiles
  for update using (auth.uid() = id);

-- 회원가입 시 자동으로 profiles 레코드 생성하는 트리거
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name, role, department)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', '정산 담당자'),
    coalesce(new.raw_user_meta_data->>'role', 'finance_manager'),
    coalesce(new.raw_user_meta_data->>'department', '병원사업본부')
  );
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();


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

-- Blog Posts RLS 활성화
alter table public.blog_posts enable row level security;

create policy "발행된 글은 누구나 조회 가능" on public.blog_posts
  for select using (is_published = true);

create policy "인증된 사용자는 글 작성 가능" on public.blog_posts
  for insert with check (auth.role() = 'authenticated');

create policy "인증된 사용자는 본인 글 수정 가능" on public.blog_posts
  for update using (auth.role() = 'authenticated');
