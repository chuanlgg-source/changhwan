#!/usr/bin/env python3
"""
run_reconcile_cli.py — 병원부 미결 통합 관리 및 리포트 CLI 실행기
GitHub Actions 및 명령행(CLI) 환경에서 파이썬 엔진을 직접 실행하고
결과 엑셀 파일 생성 및 GitHub Step Summary / 콘솔 마크다운 리포트를 출력합니다.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import reconcile_engine as eng


def format_krw(val: float | int) -> str:
    return f"{int(round(val)):,}원"


def main() -> int:
    parser = argparse.ArgumentParser(description="병원부 미결 통합 관리 및 리포트 CLI")
    parser.add_argument("--base-month", default="2026-10", help="생성 기준월 (예: 2026-10)")
    parser.add_argument("--original", default=None, help="Step 2. 원본데이터 파일 경로 (.xls / .xlsx)")
    parser.add_argument("--sahu", default=None, help="Step 3-1. 사후미결 파일 경로 (.xlsx)")
    parser.add_argument("--jeoga", default=None, help="Step 3-2. 저가미결 파일 경로 (.xlsx)")
    parser.add_argument("--yakga", default=None, help="Step 3-3. 약가미결 파일 경로 (.xls / .xlsx)")
    parser.add_argument("--sample-dir", default=str(BASE_DIR / "sample_data"), help="기본 샘플 데이터 디렉터리")
    parser.add_argument("--output-dir", default=str(BASE_DIR / "output"), help="결과물 저장 디렉터리")
    args = parser.parse_args()

    base_month = args.base_month
    sample_dir = Path(args.sample_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 파일 경로 결정 (인자 지정 우선, 없으면 sample_dir 내 자동 탐색)
    p_orig = Path(args.original) if args.original else (sample_dir / "Sample.xls")
    p_sahu = Path(args.sahu) if args.sahu else (sample_dir / "미결_병원경로_202511-202610.xlsx")
    p_jeoga = Path(args.jeoga) if args.jeoga else (sample_dir / "병원사후_미결_관리_26년_9월.xlsx")
    p_yakga = Path(args.yakga) if args.yakga else (sample_dir / "약가인하_미결_관리(병원부)S.xls")

    print(f"==================================================")
    print(f"🏥 병원부 미결 통합 관리 및 리포트 엔진 CLI")
    print(f"기준월: {base_month}")
    print(f"==================================================")
    print(f"• Step 2   원본데이터 : {p_orig}")
    print(f"• Step 3-1 사후미결   : {p_sahu}")
    print(f"• Step 3-2 저가미결   : {p_jeoga}")
    print(f"• Step 3-3 약가미결   : {p_yakga}")

    # 파일 존재 확인
    missing = [str(p) for p in (p_orig, p_sahu, p_jeoga, p_yakga) if not p.exists()]
    if missing:
        print(f"\n❌ [오류] 다음 파일을 찾을 수 없습니다:\n" + "\n".join(f"  - {f}" for f in missing))
        print("💡 sample_data 폴더에 파일을 넣거나 명령행 인자로 올바른 경로를 지정해 주세요.")
        return 1

    print("\n⏳ 1/3. 엑셀 데이터 파싱 중...")
    orig_data = eng.parse_original_sample(p_orig)
    print(f"  ✓ 원본 파싱 완료 (사후:{orig_data['counts']['sec1']}, 바슈:{orig_data['counts']['sec2']}, 저가:{orig_data['counts']['sec3']}, 약가:{orig_data['counts']['sec4']})")

    sahu_data = eng.parse_sahu_file(p_sahu)
    print(f"  ✓ 사후미결 신규 파싱 완료 ({sahu_data['count']}건)")

    jeoga_data = eng.parse_jeoga_file(p_jeoga)
    print(f"  ✓ 저가미결 신규 파싱 완료 ({jeoga_data['count']}건)")

    yakga_data = eng.parse_yakga_file(p_yakga)
    print(f"  ✓ 약가미결 신규 파싱 완료 ({yakga_data['count']}건)")

    print(f"\n⏳ 2/3. 기준월({base_month}) 기반 대사 및 통합 분석 실행 중...")
    analysis = eng.analyze_and_merge(
        orig_data,
        sahu_data,
        jeoga_data,
        yakga_data,
        base_month=base_month,
    )
    print(f"  ✓ 대사 완료: 일치건={len(analysis['settled'])}, 수정건={len(analysis['modified'])}, 신규건={len(analysis['new'])}")

    print("\n⏳ 3/3. 통합 엑셀 파일 생성 중...")
    out_name = f"미결(병원부)_통합_{base_month}.xlsx"
    out_path = output_dir / out_name
    saved_path = eng.generate_integrated_excel(analysis, out_path)
    print(f"  ✓ 엑셀 저장 완료: {saved_path}")

    # 리포트 요약 마크다운 생성
    ver = analysis.get("verification", {})
    summary_md = f"""## 🏥 병원부 미결 통합 관리 및 리포트 결과 ({base_month})

### 📊 항목별 대사 및 정합성 검증 결과
| 항목명 | 신규/수정 원본건수 | 신규/수정 원본금액 | 통합본 반영건수 | 통합본 반영금액 | 건수검증 | 금액검증 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **사후미결** | {ver.get('sec1_src_count', 0):,}건 | {format_krw(ver.get('sec1_src_sum', 0))} | {ver.get('sec1_tgt_count', 0):,}건 | {format_krw(ver.get('sec1_tgt_sum', 0))} | {'✅ 일치' if ver.get('sec1_count_match') else '❌ 불일치'} | {'✅ 일치' if ver.get('sec1_sum_match') else '❌ 불일치'} |
| **사후미결(바슈)** | {ver.get('sec2_src_count', 0):,}건 | {format_krw(ver.get('sec2_src_sum', 0))} | {ver.get('sec2_tgt_count', 0):,}건 | {format_krw(ver.get('sec2_tgt_sum', 0))} | {'✅ 일치' if ver.get('sec2_count_match') else '❌ 불일치'} | {'✅ 일치' if ver.get('sec2_sum_match') else '❌ 불일치'} |
| **저가미결** | {ver.get('sec3_src_count', 0):,}건 | {format_krw(ver.get('sec3_src_sum', 0))} | {ver.get('sec3_tgt_count', 0):,}건 | {format_krw(ver.get('sec3_tgt_sum', 0))} | {'✅ 일치' if ver.get('sec3_count_match') else '❌ 불일치'} | {'✅ 일치' if ver.get('sec3_sum_match') else '❌ 불일치'} |
| **약가미결** | {ver.get('sec4_src_count', 0):,}건 | {format_krw(ver.get('sec4_src_sum', 0))} | {ver.get('sec4_tgt_count', 0):,}건 | {format_krw(ver.get('sec4_tgt_sum', 0))} | {'✅ 일치' if ver.get('sec4_count_match') else '❌ 불일치'} | {'✅ 일치' if ver.get('sec4_sum_match') else '❌ 불일치'} |

### 📈 처리 통계
- **기존 완결/일치 건수**: {len(analysis.get('settled', [])):,}건
- **수정 반영 건수**: {len(analysis.get('modified', [])):,}건
- **신규 추가 건수**: {len(analysis.get('new', [])):,}건
- **생성된 엑셀 파일**: `{out_name}` ({os.path.getsize(saved_path):,} bytes)
"""

    print("\n" + summary_md)

    # GitHub Actions Step Summary 기록 (GitHub Actions 환경일 경우)
    step_summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary_file:
        try:
            with open(step_summary_file, "a", encoding="utf-8") as f:
                f.write(summary_md)
            print(f"✓ GitHub Step Summary 기록 완료")
        except Exception as e:
            print(f"⚠️ Step Summary 기록 중 예외: {e}")

    print("\n✅ 모든 대사 및 엑셀 생성 프로세스가 성공적으로 완료되었습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
