'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth/AuthContext';
import { supabase, isSupabaseConfigured } from '@/lib/supabase/client';
import { BlogPost } from '@/lib/supabase/mockData';
import { ArrowLeft, Save, Sparkles, AlertCircle } from 'lucide-react';

export default function BlogWritePage() {
  const router = useRouter();
  const { user } = useAuth();

  const [title, setTitle] = useState('');
  const [category, setCategory] = useState<'공지' | '업무가이드' | '정산리포트' | '시스템개선'>('공지');
  const [summary, setSummary] = useState('');
  const [tags, setTags] = useState('병원부, 정산, 업무공유');
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) {
      setErrorMsg('제목과 본문을 모두 입력해주세요.');
      return;
    }

    setSaving(true);
    setErrorMsg('');

    const parsedTags = tags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    const newPost: BlogPost = {
      id: 'post-' + Date.now(),
      title,
      category,
      author: user?.name || '담당자',
      authorRole: user?.role === 'admin' ? '시스템 관리자' : '정산 담당자',
      date: new Date().toISOString().substring(0, 10),
      summary: summary || title,
      content,
      views: 1,
      tags: parsedTags.length > 0 ? parsedTags : ['일반'],
    };

    // 1. Supabase 연동 시 DB INSERT
    if (isSupabaseConfigured && supabase) {
      const { error } = await supabase.from('blog_posts').insert([
        {
          title: newPost.title,
          slug: 'post-' + Date.now(),
          category: newPost.category,
          author_name: newPost.author,
          author_role: newPost.authorRole,
          summary: newPost.summary,
          content: newPost.content,
          tags: newPost.tags,
          is_published: true,
          view_count: 1,
        },
      ]);
      if (error) {
        console.error('Supabase write error:', error);
      }
    }

    // 2. LocalStorage에도 동기화 (데모 환경 즉시 반영)
    if (typeof window !== 'undefined') {
      const existing = localStorage.getItem('clp_custom_blog_posts');
      const list = existing ? JSON.parse(existing) : [];
      list.unshift(newPost);
      localStorage.setItem('clp_custom_blog_posts', JSON.stringify(list));
    }

    setSaving(false);
    router.push('/portal/blog');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <Link
          href="/portal/blog"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#1e3a8a] hover:underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>목록으로 돌아가기</span>
        </Link>
      </div>

      <div className="bg-white rounded-xl border border-[#cbd5e1] shadow-stitch-card p-6 sm:p-8">
        <div className="border-b border-[#e2e8f0] pb-4 mb-6">
          <h1 className="text-xl font-bold font-headline text-[#00236f] tracking-tight">
            새 업무 지식 / 공지사항 작성
          </h1>
          <p className="text-xs text-[#757682] mt-1">
            사내 포털 구성원에게 공유할 공지나 업무 가이드를 등록합니다.
          </p>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 rounded bg-[#fef2f2] border border-[#fecaca] text-[#dc2626] text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-[#131b2e] mb-1.5">
                게시글 제목 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="예: 2026년 4분기 공급 실적 정산 마감 안내"
                className="w-full px-3 py-2 text-xs bg-[#faf8ff] border border-[#cbd5e1] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1e3a8a] focus:bg-white text-[#131b2e]"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-[#131b2e] mb-1.5">
                카테고리 구분
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as any)}
                className="w-full px-3 py-2 text-xs bg-[#faf8ff] border border-[#cbd5e1] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1e3a8a] focus:bg-white text-[#131b2e]"
              >
                <option value="공지">공지</option>
                <option value="업무가이드">업무가이드</option>
                <option value="정산리포트">정산리포트</option>
                <option value="시스템개선">시스템개선</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-[#131b2e] mb-1.5">
              목록 요약문 (선택)
            </label>
            <input
              type="text"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              placeholder="목록 카드에 노출될 간략한 요약 설명 1~2줄"
              className="w-full px-3 py-2 text-xs bg-[#faf8ff] border border-[#cbd5e1] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1e3a8a] focus:bg-white text-[#131b2e]"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-[#131b2e] mb-1.5">
              태그 (쉼표로 구분)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="예: 정산마감, 병원부, 원장대사"
              className="w-full px-3 py-2 text-xs bg-[#faf8ff] border border-[#cbd5e1] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1e3a8a] focus:bg-white text-[#131b2e]"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-[#131b2e] mb-1.5">
              본문 내용 (마크다운 지원) <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={12}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="## 1. 개요&#10;공유할 내용을 작성해주세요..."
              className="w-full p-3 text-xs bg-[#faf8ff] border border-[#cbd5e1] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1e3a8a] focus:bg-white text-[#131b2e] font-sans leading-relaxed"
              required
            ></textarea>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#e2e8f0]">
            <Link
              href="/portal/blog"
              className="px-4 py-2 border border-[#cbd5e1] text-[#444651] text-xs font-semibold rounded-md hover:bg-[#f1f5f9] transition"
            >
              취소
            </Link>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 bg-[#00236f] hover:bg-[#1e3a8a] text-white text-xs font-bold rounded-md shadow transition flex items-center gap-1.5 disabled:opacity-60 cursor-pointer"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{saving ? '저장 중...' : '게시글 등록하기'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
