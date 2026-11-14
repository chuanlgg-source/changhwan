'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { initialBlogPosts, BlogPost } from '@/lib/supabase/mockData';
import { supabase, isSupabaseConfigured } from '@/lib/supabase/client';
import {
  ArrowLeft,
  Calendar,
  User,
  Eye,
  Tag,
  Share2,
  Printer,
  BookOpen
} from 'lucide-react';

export default function BlogPostDetailPage() {
  const params = useParams();
  const router = useRouter();
  const postId = params.id as string;
  const [post, setPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Supabase 조회
    if (isSupabaseConfigured && supabase) {
      supabase
        .from('blog_posts')
        .select('*')
        .eq('id', postId)
        .single()
        .then(({ data, error }) => {
          if (!error && data) {
            setPost({
              id: data.id,
              title: data.title,
              category: data.category || '공지',
              author: data.author_name || '관리자',
              authorRole: data.author_role || '매니저',
              date: data.created_at ? data.created_at.substring(0, 10) : '2026-11-13',
              summary: data.summary || '',
              content: data.content || '',
              views: (data.view_count || 0) + 1,
              tags: data.tags || ['사내업무'],
            });
          } else {
            fallbackLocal();
          }
          setLoading(false);
        });
    } else {
      fallbackLocal();
      setLoading(false);
    }

    function fallbackLocal() {
      // 로컬 스토리지 확인
      let allPosts = initialBlogPosts;
      if (typeof window !== 'undefined') {
        const localAdded = localStorage.getItem('clp_custom_blog_posts');
        if (localAdded) {
          try {
            allPosts = [...JSON.parse(localAdded), ...initialBlogPosts];
          } catch {}
        }
      }
      const found = allPosts.find((p) => p.id === postId);
      if (found) {
        setPost({ ...found, views: found.views + 1 });
      }
    }
  }, [postId]);

  if (loading) {
    return (
      <div className="p-12 text-center text-xs text-[#757682]">
        게시글을 불러오는 중입니다...
      </div>
    );
  }

  if (!post) {
    return (
      <div className="bg-white rounded-xl border border-[#cbd5e1] p-12 text-center space-y-4">
        <h2 className="text-base font-bold text-[#00236f]">게시글을 찾을 수 없습니다.</h2>
        <p className="text-xs text-[#757682]">삭제되었거나 잘못된 경로입니다.</p>
        <Link
          href="/portal/blog"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#00236f] text-white text-xs font-semibold rounded-md"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>블로그 목록으로 돌아가기</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <Link
          href="/portal/blog"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#1e3a8a] hover:underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>전체 게시글 목록으로</span>
        </Link>
      </div>

      {/* Article Container */}
      <article className="bg-white rounded-xl border border-[#cbd5e1] shadow-stitch-card overflow-hidden">
        {/* Header Banner */}
        <div className="p-6 sm:p-8 border-b border-[#e2e8f0] bg-[#faf8ff]">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-[11px] font-bold px-2.5 py-0.5 rounded bg-[#eff6ff] text-[#2563eb] border border-[#bfdbfe]">
              {post.category}
            </span>
            <span className="text-xs text-[#757682] flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              <span>{post.date}</span>
            </span>
          </div>

          <h1 className="text-xl sm:text-2xl font-bold font-headline text-[#00236f] tracking-tight leading-snug">
            {post.title}
          </h1>

          <div className="flex flex-wrap items-center justify-between gap-3 mt-4 pt-4 border-t border-[#e2e8f0] text-xs text-[#444651]">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-[#1e3a8a] text-white flex items-center justify-center font-bold text-xs">
                {post.author.charAt(0)}
              </div>
              <div>
                <span className="font-semibold text-[#131b2e]">{post.author}</span>
                <span className="text-[#757682] ml-1.5">({post.authorRole})</span>
              </div>
            </div>

            <div className="flex items-center gap-4 text-[#757682]">
              <span className="flex items-center gap-1">
                <Eye className="w-3.5 h-3.5" />
                <span>조회 {post.views}</span>
              </span>
              <button
                onClick={() => {
                  if (typeof window !== 'undefined') window.print();
                }}
                title="인쇄"
                className="hover:text-[#00236f] transition"
              >
                <Printer className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 sm:p-8 text-[#131b2e] text-sm leading-relaxed whitespace-pre-wrap font-sans">
          {post.content}
        </div>

        {/* Tags & Footer */}
        <div className="p-6 bg-[#faf8ff] border-t border-[#e2e8f0] flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 flex-wrap">
            <Tag className="w-3.5 h-3.5 text-[#757682]" />
            {post.tags.map((tag, idx) => (
              <span
                key={idx}
                className="text-xs px-2.5 py-0.5 rounded-full bg-white border border-[#cbd5e1] text-[#475569] font-medium"
              >
                #{tag}
              </span>
            ))}
          </div>

          <Link
            href="/portal/blog/write"
            className="text-xs font-semibold text-[#1e3a8a] hover:underline"
          >
            + 새 글 작성하기
          </Link>
        </div>
      </article>
    </div>
  );
}
