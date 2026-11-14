'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth/AuthContext';
import { initialBlogPosts, BlogPost } from '@/lib/supabase/mockData';
import { supabase, isSupabaseConfigured } from '@/lib/supabase/client';
import {
  BookOpen,
  Search,
  PenSquare,
  Calendar,
  User,
  Eye,
  Tag,
  ChevronRight,
  Database
} from 'lucide-react';

const CATEGORIES = ['전체', '공지', '업무가이드', '정산리포트', '시스템개선'];

export default function BlogListPage() {
  const { user } = useAuth();
  const [posts, setPosts] = useState<BlogPost[]>(initialBlogPosts);
  const [selectedCategory, setSelectedCategory] = useState('전체');
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingPosts, setLoadingPosts] = useState(false);

  useEffect(() => {
    // Supabase 연동 시 DB에서 조회 시도
    if (isSupabaseConfigured && supabase) {
      setLoadingPosts(true);
      supabase
        .from('blog_posts')
        .select('*')
        .order('created_at', { ascending: false })
        .then(({ data, error }) => {
          setLoadingPosts(false);
          if (!error && data && data.length > 0) {
            const mapped: BlogPost[] = data.map((item) => ({
              id: item.id,
              title: item.title,
              category: item.category || '공지',
              author: item.author_name || '관리자',
              authorRole: item.author_role || '매니저',
              date: item.created_at ? item.created_at.substring(0, 10) : '2026-11-13',
              summary: item.summary || '',
              content: item.content || '',
              views: item.view_count || 0,
              tags: item.tags || ['사내업무'],
            }));
            setPosts(mapped);
          }
        });
    } else {
      // 로컬 스토리지에 저장된 추가 글이 있는지 확인
      if (typeof window !== 'undefined') {
        const localAdded = localStorage.getItem('clp_custom_blog_posts');
        if (localAdded) {
          try {
            const parsed = JSON.parse(localAdded);
            setPosts([...parsed, ...initialBlogPosts]);
          } catch {
            setPosts(initialBlogPosts);
          }
        }
      }
    }
  }, []);

  const filteredPosts = posts.filter((post) => {
    const matchesCategory =
      selectedCategory === '전체' || post.category === selectedCategory;
    const matchesSearch =
      post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      post.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Blog Page Header */}
      <div className="bg-white rounded-xl border border-[#cbd5e1] p-6 shadow-stitch-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#1e3a8a] mb-1">
            <BookOpen className="w-4 h-4" />
            <span>KNOWLEDGE & BLOG HUB</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold font-headline text-[#00236f] tracking-tight">
            업무 지식 블로그 & 공지사항
          </h1>
          <p className="text-xs text-[#444651] mt-1">
            정산 원장 대사 매뉴얼, 분기 마감 일정, 시스템 사용 팁을 공유하는 통합 지식 저장소입니다.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/portal/blog/write"
            className="px-4 py-2 bg-[#00236f] hover:bg-[#1e3a8a] text-white text-xs font-bold rounded-md transition flex items-center gap-1.5 shadow"
          >
            <PenSquare className="w-3.5 h-3.5" />
            <span>새 글 작성하기</span>
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-3 rounded-lg border border-[#cbd5e1] shadow-stitch-card">
        {/* Category Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-[#1e3a8a] text-white'
                  : 'text-[#444651] hover:bg-[#f1f5f9] hover:text-[#00236f]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-[#757682] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="제목, 내용, 태그 검색..."
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-[#faf8ff] border border-[#cbd5e1] rounded-md focus:outline-none focus:ring-1 focus:ring-[#1e3a8a] text-[#131b2e]"
          />
        </div>
      </div>

      {/* Post List */}
      <div className="space-y-4">
        {loadingPosts ? (
          <div className="p-12 text-center text-xs text-[#757682]">
            게시글을 불러오는 중입니다...
          </div>
        ) : filteredPosts.length === 0 ? (
          <div className="bg-white rounded-lg border border-[#cbd5e1] p-12 text-center text-xs text-[#757682]">
            검색 결과와 일치하는 게시글이 없습니다.
          </div>
        ) : (
          filteredPosts.map((post) => (
            <article
              key={post.id}
              className="bg-white rounded-lg border border-[#cbd5e1] p-5 shadow-stitch-card hover:border-[#1e3a8a] hover:shadow-stitch-elevated transition"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                      post.category === '공지'
                        ? 'bg-[#eff6ff] text-[#2563eb] border-[#bfdbfe]'
                        : post.category === '업무가이드'
                        ? 'bg-[#ecfdf5] text-[#059669] border-[#a7f3d0]'
                        : post.category === '정산리포트'
                        ? 'bg-[#fffbeb] text-[#d97706] border-[#fde68a]'
                        : 'bg-[#f5f3ff] text-[#7c3aed] border-[#ddd6fe]'
                    }`}
                  >
                    {post.category}
                  </span>
                  <div className="flex items-center gap-1 text-[11px] text-[#757682]">
                    <Calendar className="w-3 h-3" />
                    <span>{post.date}</span>
                  </div>
                  <div className="flex items-center gap-1 text-[11px] text-[#757682] ml-2">
                    <User className="w-3 h-3" />
                    <span>{post.author} ({post.authorRole})</span>
                  </div>
                </div>

                <div className="flex items-center gap-1 text-[11px] text-[#757682]">
                  <Eye className="w-3 h-3" />
                  <span>조회 {post.views}</span>
                </div>
              </div>

              <Link href={`/portal/blog/${post.id}`}>
                <h2 className="text-base font-bold font-headline text-[#00236f] hover:text-[#1e3a8a] transition tracking-tight">
                  {post.title}
                </h2>
              </Link>

              <p className="text-xs text-[#444651] mt-2 line-clamp-2 leading-relaxed">
                {post.summary}
              </p>

              <div className="flex flex-wrap items-center justify-between gap-3 mt-4 pt-3 border-t border-[#f1f5f9]">
                <div className="flex flex-wrap items-center gap-1.5">
                  <Tag className="w-3 h-3 text-[#757682]" />
                  {post.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] px-2 py-0.5 rounded-full bg-[#f1f5f9] text-[#475569] font-medium"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>

                <Link
                  href={`/portal/blog/${post.id}`}
                  className="text-xs font-semibold text-[#1e3a8a] hover:underline flex items-center gap-1"
                >
                  <span>본문 전체 읽기</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </article>
          ))
        )}
      </div>
    </div>
  );
}
