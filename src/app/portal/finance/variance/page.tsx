'use client';

import React from 'react';
import { TrendingDown, AlertTriangle, ShieldCheck, Download, BarChart2 } from 'lucide-react';

export default function VarianceAnalysisPage() {
  const VARIANCE_DATA = [
    { hospital: '세브란스병원', code: 'H02', diff: 25000000, reason: '납품 단가 정산 승인 대기', status: '소명진행중' },
    { hospital: '삼성서울병원', code: 'H04', diff: 18200000, reason: '계약 할인율 3.2% 사후 반영분 차액', status: '검토완료' },
    { hospital: '분당서울대병원', code: 'H08', diff: 8500000, reason: '반품 물량 검수 지연으로 인한 잔액', status: '확인필요' },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-[#cbd5e1] p-6 shadow-stitch-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#1e3a8a] mb-1">
            <BarChart2 className="w-4 h-4" />
            <span>VARIANCE & DISCREPANCY AUDIT</span>
          </div>
          <h1 className="text-xl font-bold font-headline text-[#00236f] tracking-tight">
            월별 차액 분석 현황 (신규 코딩 하위메뉴)
          </h1>
          <p className="text-xs text-[#757682] mt-1">
            약정 할인율, 반품 내역, 입고 검수 차이로 인해 발생한 미결 차액 항목 정밀 추적
          </p>
        </div>

        <button
          onClick={() => alert('엑셀 보고서 다운로드 기능이 준비되었습니다.')}
          className="px-4 py-2 border border-[#cbd5e1] hover:bg-[#f1f5f9] text-[#131b2e] text-xs font-bold rounded-md transition flex items-center gap-1.5"
        >
          <Download className="w-3.5 h-3.5 text-[#1e3a8a]" />
          <span>차액 분석서 다운로드</span>
        </button>
      </div>

      <div className="bg-white rounded-xl border border-[#cbd5e1] shadow-stitch-card p-6">
        <h2 className="text-sm font-bold font-headline text-[#00236f] mb-4">
          미결 차액 세부 소명 내역
        </h2>

        <div className="space-y-3">
          {VARIANCE_DATA.map((item, idx) => (
            <div
              key={idx}
              className="p-4 rounded-lg border border-[#e2e8f0] bg-[#faf8ff] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-[#fef2f2] text-[#dc2626] flex items-center justify-center font-bold text-xs">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-[#131b2e] flex items-center gap-2">
                    <span>{item.hospital}</span>
                    <span className="font-mono text-[11px] text-[#757682]">({item.code})</span>
                  </div>
                  <div className="text-[11px] text-[#444651] mt-0.5">
                    사유: {item.reason}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-xs font-bold font-mono text-[#dc2626] num-font">
                    ₩ {item.diff.toLocaleString('ko-KR')}
                  </div>
                  <span className="text-[10px] text-[#757682]">차액 발생금</span>
                </div>

                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#fffbeb] text-[#d97706] border border-[#fde68a]">
                  {item.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
