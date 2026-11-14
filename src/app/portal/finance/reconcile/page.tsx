'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  FileSpreadsheet,
  Maximize2,
  ExternalLink,
  ChevronLeft,
  Info
} from 'lucide-react';

export default function ReconcileLedgerPage() {
  const [fullscreen, setFullscreen] = useState(false);

  return (
    <div className={`space-y-4 ${fullscreen ? 'fixed inset-0 z-50 bg-white p-4' : ''}`}>
      {/* Header Bar */}
      <div className="bg-white rounded-xl border border-[#cbd5e1] p-4 shadow-stitch-card flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#1e3a8a] text-white flex items-center justify-center">
            <FileSpreadsheet className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-base font-bold font-headline text-[#00236f]">
              병원부 미결 통합 원장 대사 (Reconciliation Engine)
            </h1>
            <p className="text-[11px] text-[#757682]">
              정산 원장 대사 엔진(Pyodide WebAssembly)이 결합된 고정밀 전산 워크스페이스
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setFullscreen(!fullscreen)}
            className="px-3 py-1.5 border border-[#cbd5e1] text-[#131b2e] text-xs font-semibold rounded hover:bg-[#f1f5f9] transition flex items-center gap-1.5"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            <span>{fullscreen ? '포털 축소 보기' : '전체화면 확대'}</span>
          </button>

          <a
            href="/legacy/reconcile_ui.html"
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 bg-[#00236f] text-white text-xs font-semibold rounded hover:bg-[#1e3a8a] transition flex items-center gap-1.5 shadow"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            <span>새 탭에서 열기</span>
          </a>
        </div>
      </div>

      {/* Embedded Iframe Container */}
      <div className="bg-white rounded-xl border border-[#cbd5e1] shadow-stitch-card overflow-hidden">
        <iframe
          src="/legacy/reconcile_ui.html"
          title="병원부 미결 통합 원장 대사"
          className="w-full border-0"
          style={{ height: fullscreen ? 'calc(100vh - 100px)' : '820px' }}
        />
      </div>
    </div>
  );
}
