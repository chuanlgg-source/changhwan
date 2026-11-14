'use client';

import React, { useState } from 'react';
import { Calculator, Maximize2, ExternalLink } from 'lucide-react';

export default function SavingsSimulatorPage() {
  const [fullscreen, setFullscreen] = useState(false);

  return (
    <div className={`space-y-4 ${fullscreen ? 'fixed inset-0 z-50 bg-white p-4' : ''}`}>
      <div className="bg-white rounded-xl border border-[#cbd5e1] p-4 shadow-stitch-card flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#059669] text-white flex items-center justify-center">
            <Calculator className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-base font-bold font-headline text-[#00236f]">
              적금 및 수익률 정밀 시뮬레이터
            </h1>
            <p className="text-[11px] text-[#757682]">
              단리/복리, 일반과세·세금우대·비과세 조건별 만기 수령액 시뮬레이션
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
            href="/legacy/savings-simulator.html"
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 bg-[#00236f] text-white text-xs font-semibold rounded hover:bg-[#1e3a8a] transition flex items-center gap-1.5 shadow"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            <span>새 탭에서 열기</span>
          </a>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-[#cbd5e1] shadow-stitch-card overflow-hidden">
        <iframe
          src="/legacy/savings-simulator.html"
          title="적금 및 수익률 정밀 시뮬레이터"
          className="w-full border-0"
          style={{ height: fullscreen ? 'calc(100vh - 100px)' : '780px' }}
        />
      </div>
    </div>
  );
}
