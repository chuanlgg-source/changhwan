'use client';

import React from 'react';
import Link from 'next/link';
import { PieChart, Calculator, ArrowRight, ShieldCheck, Percent, Landmark } from 'lucide-react';

export default function ToolsOverviewPage() {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-[#cbd5e1] p-6 shadow-stitch-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#1e3a8a] mb-1">
            <PieChart className="w-4 h-4" />
            <span>FINANCIAL CALCULATION SUITE</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold font-headline text-[#00236f] tracking-tight">
            금융 시뮬레이션 및 자산 도구 개요
          </h1>
          <p className="text-xs text-[#444651] mt-1">
            단리/복리 이자 계산, 비과세 종합저축 시뮬레이터 및 현금흐름 분석 도구
          </p>
        </div>

        <Link
          href="/portal/tools/simulator"
          className="px-4 py-2 bg-[#00236f] hover:bg-[#1e3a8a] text-white text-xs font-bold rounded-md transition flex items-center gap-1.5 shadow"
        >
          <Calculator className="w-3.5 h-3.5" />
          <span>적금 시뮬레이터 실행</span>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-[#cbd5e1] p-6 shadow-stitch-card flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-lg bg-[#ecfdf5] text-[#059669] flex items-center justify-center mb-3">
              <Percent className="w-5 h-5" />
            </div>
            <h2 className="text-base font-bold font-headline text-[#00236f]">
              적금 & 수익률 시뮬레이터 v2.0
            </h2>
            <p className="text-xs text-[#444651] mt-2 leading-relaxed">
              월 정기 적립금, 금리(단리/월복리), 세금 유형(일반과세 15.4%, 세금우대 9.5%, 비과세 0%)을 동적으로 조절하여 만기 수령액 및 실질 이자율을 그래프와 함께 실시간 계산합니다.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-[#e2e8f0]">
            <Link
              href="/portal/tools/simulator"
              className="w-full py-2 bg-[#1e3a8a] hover:bg-[#00236f] text-white text-xs font-bold rounded-md flex items-center justify-center gap-1.5 transition"
            >
              <span>시뮬레이터 열기</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-[#cbd5e1] p-6 shadow-stitch-card flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-lg bg-[#eff6ff] text-[#2563eb] flex items-center justify-center mb-3">
              <Landmark className="w-5 h-5" />
            </div>
            <h2 className="text-base font-bold font-headline text-[#00236f]">
              자금 운용 및 이자율 가이드
            </h2>
            <p className="text-xs text-[#444651] mt-2 leading-relaxed">
              병원부 운영 자금 단기 예치 및 유동성 관리를 위한 최신 수신 금리 동향과 이자 소득세 절세 팁을 제공합니다.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-[#e2e8f0]">
            <Link
              href="/portal/blog"
              className="w-full py-2 bg-[#f2f3ff] hover:bg-[#eaedff] text-[#1e3a8a] text-xs font-bold rounded-md flex items-center justify-center gap-1.5 transition"
            >
              <span>관련 업무 가이드 열람</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
