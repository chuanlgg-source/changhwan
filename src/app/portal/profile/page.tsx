'use client';

import React from 'react';
import { User, ExternalLink, ShieldCheck, Mail, Building, Phone } from 'lucide-react';

export default function ProfilePage() {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-[#cbd5e1] p-6 shadow-stitch-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#1e3a8a] mb-1">
            <User className="w-4 h-4" />
            <span>EXECUTIVE PROFILE & CARD</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold font-headline text-[#00236f] tracking-tight">
            이창환 총괄 매니저 프로필 (디지털 명함)
          </h1>
          <p className="text-xs text-[#444651] mt-1">
            병원 제약 공급망 정산 및 전산화 총괄 담당자 프로필 카드
          </p>
        </div>

        <a
          href="/legacy/business-card.html"
          target="_blank"
          rel="noreferrer"
          className="px-4 py-2 bg-[#00236f] hover:bg-[#1e3a8a] text-white text-xs font-bold rounded-md transition flex items-center gap-1.5 shadow"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          <span>디지털 명함 풀스크린 보기</span>
        </a>
      </div>

      <div className="bg-white rounded-xl border border-[#cbd5e1] shadow-stitch-card overflow-hidden">
        <iframe
          src="/legacy/business-card.html"
          title="이창환 디지털 명함"
          className="w-full border-0"
          style={{ height: '760px' }}
        />
      </div>
    </div>
  );
}
