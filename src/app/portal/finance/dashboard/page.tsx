'use client';

import React from 'react';
import Link from 'next/link';
import {
  TrendingUp,
  FileCheck2,
  AlertCircle,
  FileSpreadsheet,
  ArrowRight,
  Building,
  RefreshCw,
  Download
} from 'lucide-react';

const HOSPITAL_SUMMARY = [
  { code: 'H01', name: '서울대병원', expected: 320000000, executed: 320000000, unsettled: 0, status: '완결', statusColor: 'settled' },
  { code: 'H02', name: '세브란스병원', expected: 285000000, executed: 260000000, unsettled: 25000000, status: '미결', statusColor: 'critical' },
  { code: 'H03', name: '아산병원', expected: 410000000, executed: 410000000, unsettled: 0, status: '완결', statusColor: 'settled' },
  { code: 'H04', name: '삼성서울병원', expected: 345000000, executed: 326800000, unsettled: 18200000, status: '차액조정', statusColor: 'modified' },
  { code: 'H05', name: '고려대안암병원', expected: 122900000, executed: 122900000, unsettled: 0, status: '완결', statusColor: 'settled' },
];

export default function FinanceDashboardPage() {
  const formatKrw = (val: number) => {
    return '₩ ' + val.toLocaleString('ko-KR');
  };

  return (
    <div className="space-y-6">
      {/* Dashboard Top Header */}
      <div className="bg-white rounded-xl border border-[#cbd5e1] p-6 shadow-stitch-card flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#1e3a8a] mb-1">
            <Building className="w-4 h-4" />
            <span>FINANCIAL OPERATIONS DASHBOARD</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold font-headline text-[#00236f] tracking-tight">
            병원부 미결 정산 총괄 대시보드
          </h1>
          <p className="text-xs text-[#444651] mt-1">
            기준월 2026년 11월 기준 | 병원 제약 공급망 정산 및 미결 차액 현황 모니터링
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            href="/portal/finance/reconcile"
            className="px-4 py-2 bg-[#00236f] hover:bg-[#1e3a8a] text-white text-xs font-bold rounded-md transition flex items-center gap-1.5 shadow"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>원장 대사 화면으로 이동</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-lg border border-[#cbd5e1] shadow-stitch-card border-l-4 border-l-[#1e3a8a]">
          <div className="text-xs text-[#757682] font-semibold">총 정산 예정금액</div>
          <div className="text-2xl font-bold font-mono text-[#00236f] mt-1 num-font">
            ₩ 1,482,900,000
          </div>
          <div className="text-[11px] text-[#444651] mt-1">총 5개 주요 수탁 병원</div>
        </div>

        <div className="bg-white p-5 rounded-lg border border-[#cbd5e1] shadow-stitch-card border-l-4 border-l-[#059669]">
          <div className="text-xs text-[#757682] font-semibold">실제 집행 확정액 (완결)</div>
          <div className="text-2xl font-bold font-mono text-[#059669] mt-1 num-font">
            ₩ 1,439,700,000
          </div>
          <div className="text-[11px] text-[#059669] font-medium mt-1">집행 완료율 97.1%</div>
        </div>

        <div className="bg-white p-5 rounded-lg border border-[#cbd5e1] shadow-stitch-card border-l-4 border-l-[#dc2626]">
          <div className="text-xs text-[#757682] font-semibold">미결 잔액 (소명 대기)</div>
          <div className="text-2xl font-bold font-mono text-[#dc2626] mt-1 num-font">
            ₩ 43,200,000
          </div>
          <div className="text-[11px] text-[#dc2626] font-medium mt-1">2개 병원 원장 확인 요망</div>
        </div>
      </div>

      {/* Clinical Ledger Density Table */}
      <div className="bg-white rounded-xl border border-[#cbd5e1] shadow-stitch-card overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-[#e2e8f0] flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold font-headline text-[#00236f]">
              주요 병원별 11월 정산 대사 현황표
            </h2>
            <p className="text-[11px] text-[#757682]">
              Clinical Ledger Precision 고밀도 수치 정렬 (Tabular-nums)
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-[#757682]">최근 전산 갱신: 방금 전</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#f2f3ff] border-b border-[#cbd5e1] text-[11px] font-bold text-[#1e3a8a] uppercase">
                <th className="py-2.5 px-4">기관코드</th>
                <th className="py-2.5 px-4">병원명</th>
                <th className="py-2.5 px-4 text-right">예정금액</th>
                <th className="py-2.5 px-4 text-right">집행금액</th>
                <th className="py-2.5 px-4 text-right">미결차액</th>
                <th className="py-2.5 px-4 text-center">정산상태</th>
                <th className="py-2.5 px-4 text-center">액션</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e2e8f0] text-xs">
              {HOSPITAL_SUMMARY.map((row) => (
                <tr key={row.code} className="hover:bg-[#faf8ff] transition h-9">
                  <td className="py-2 px-4 font-mono font-semibold text-[#1e3a8a] text-[11px]">
                    {row.code}
                  </td>
                  <td className="py-2 px-4 font-semibold text-[#131b2e]">
                    {row.name}
                  </td>
                  <td className="py-2 px-4 text-right font-mono num-font text-[#444651]">
                    {formatKrw(row.expected)}
                  </td>
                  <td className="py-2 px-4 text-right font-mono num-font font-semibold text-[#00236f]">
                    {formatKrw(row.executed)}
                  </td>
                  <td className="py-2 px-4 text-right font-mono num-font font-bold">
                    {row.unsettled > 0 ? (
                      <span className="text-[#dc2626]">{formatKrw(row.unsettled)}</span>
                    ) : (
                      <span className="text-[#059669]">₩ 0</span>
                    )}
                  </td>
                  <td className="py-2 px-4 text-center">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                        row.statusColor === 'settled'
                          ? 'bg-[#ecfdf5] text-[#059669] border-[#a7f3d0]'
                          : row.statusColor === 'critical'
                          ? 'bg-[#fef2f2] text-[#dc2626] border-[#fecaca]'
                          : 'bg-[#fffbeb] text-[#d97706] border-[#fde68a]'
                      }`}
                    >
                      {row.status}
                    </span>
                  </td>
                  <td className="py-2 px-4 text-center">
                    <Link
                      href="/portal/finance/reconcile"
                      className="text-[11px] font-semibold text-[#1e3a8a] hover:underline"
                    >
                      상세 대사
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="p-3 bg-[#faf8ff] border-t border-[#e2e8f0] flex items-center justify-between text-xs text-[#757682]">
          <span>전체 5개 거래선 집계 완료</span>
          <Link
            href="/portal/finance/variance"
            className="text-[#1e3a8a] font-semibold hover:underline flex items-center gap-1"
          >
            <span>월별 차액 분석 보고서 조회</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
