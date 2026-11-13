"""
reconcile_engine.py — 병원부 미결 통합 관리 및 리포트 엔진
1. 생성 기준월 선택
2. 원본데이터 (Sample.xls) 로드 (4대 섹션 구조 파싱)
3. 수정 및 신규데이터 3종 로드:
   - 2-1. 사후미결 (미결_병원경로_202511-202610.xlsx)
   - 2-2. 저가미결 (병원사후_미결_관리_26년_9월.xlsx)
   - 2-3. 약가미결 (약가인하_미결_관리(병원부)S.xls)
4. 비교·수정·신규 통합 및 매입처별 요약 리포트 생성
5. 업데이트된 엑셀파일 생성 (Sample.xls의 4섹션 구조 유지 + Clinical Ledger Precision 디자인 재구성)
"""
from __future__ import annotations

import datetime
import math
import os
import re
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import xlrd


# ──────────────────────────────────────────────────────────────
# 공통 유틸리티 (날짜 / 코드 / 숫자 정규화)
# ──────────────────────────────────────────────────────────────
def clean_code(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, float):
        if math.isnan(val):
            return ""
        if val.is_integer():
            return str(int(val))
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def clean_num(val: Any) -> float:
    if val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        if math.isnan(val):
            return 0.0
        return float(val)
    s = str(val).replace(",", "").strip()
    if not s or s.startswith("="):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_date_str(val: Any) -> str:
    """엑셀 시리얼 번호, datetime, 'YY/MM', 'YYYY-MM-DD' 등을 'YYYY-MM-DD' 문자열로 변환."""
    if val is None or val == "":
        return ""
    if isinstance(val, datetime.datetime):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, datetime.date):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, (int, float)):
        if val > 30000:
            dt = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=int(round(val)))
            return dt.strftime("%Y-%m-%d")
        return ""
    s = str(val).strip()
    if not s or s == "0" or s == "0.0":
        return ""
    # '26/08' 형태
    m = re.match(r"^(\d{2})/(\d{2})$", s)
    if m:
        return f"20{m.group(1)}-{m.group(2)}-01"
    # '202601' 형태
    m2 = re.match(r"^(\d{4})(\d{2})$", s)
    if m2:
        return f"{m2.group(1)}-{m2.group(2)}-01"
    # '2026-08-26 00:00:00' 형태
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    # 숫자형 문자열 ('46235.0')
    try:
        f = float(s)
        if f > 30000:
            dt = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=int(round(f)))
            return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    return s


def parse_ym(val: Any) -> str:
    """임의 날짜/문자열에서 'YYYY-MM' 추출."""
    d = parse_date_str(val)
    if len(d) >= 7 and d[4] == "-":
        return d[:7]
    s = str(val or "").strip()
    m = re.match(r"^(\d{2})/(\d{2})$", s)
    if m:
        return f"20{m.group(1)}-{m.group(2)}"
    return ""


def ym_to_yy_slash_mm(ym: str) -> str:
    """'2026-08' -> '26/08'"""
    if len(ym) >= 7 and ym[4] == "-":
        return f"{ym[2:4]}/{ym[5:7]}"
    return ym


def read_sheet_rows(filepath: str | Path, sheet_name: str | int = 0) -> list[list[Any]]:
    """확장자(.xls / .xlsx)에 관계없이 시트의 모든 행을 2차원 리스트로 반환 (수식이 아닌 값 기준)."""
    p = str(filepath)
    if p.lower().endswith(".xls"):
        wb = xlrd.open_workbook(p)
        ws = wb.sheet_by_index(sheet_name) if isinstance(sheet_name, int) else wb.sheet_by_name(sheet_name)
        rows = []
        for r in range(ws.nrows):
            rows.append([ws.cell_value(r, c) for c in range(ws.ncols)])
        return rows
    else:
        wb = openpyxl.load_workbook(p, data_only=True)
        ws = wb.worksheets[sheet_name] if isinstance(sheet_name, int) else wb[sheet_name]
        rows = []
        for row in ws.iter_rows(values_only=True):
            rows.append(list(row))
        return rows


def get_sheet_names(filepath: str | Path) -> list[str]:
    p = str(filepath)
    if p.lower().endswith(".xls"):
        return xlrd.open_workbook(p).sheet_names()
    return openpyxl.load_workbook(p, read_only=True).sheetnames


# ──────────────────────────────────────────────────────────────
# 섹션별 표준 컬럼 정의 (Sample.xls 4대 섹션 완벽 호환)
# ──────────────────────────────────────────────────────────────
COMMON_20_COLS = [
    "코드", "매입월", "매입처", "매입처명", "조건",
    "사전%", "매입%", "수금%", "년%", "일자",
    "적요", "예정금액", "발행일자", "내용", "금액",
    "미결금액", "거래처", "비고", "거래코드", "거래처명"
]

SEC1_COLS = COMMON_20_COLS + ["자료비고"]
SEC2_COLS = COMMON_20_COLS
SEC3_COLS = COMMON_20_COLS + ["참조", "참조-현 내역", "예정 차", "미결 차", "잡행일", "완결"]
SEC4_COLS = COMMON_20_COLS + ["공란1", "공란2", "공란3", "오차분", "잡행일"]


# ──────────────────────────────────────────────────────────────
# 1. 원본 데이터 (Sample.xls) 파서
# ──────────────────────────────────────────────────────────────
def parse_original_sample(filepath: str | Path) -> dict[str, Any]:
    rows = read_sheet_rows(filepath, 0)
    sections: dict[str, list[dict[str, Any]]] = {
        "sec1": [],  # 사후/수금/매입할인 미결
        "sec2": [],  # 바슈헬스코리아(솔타) 예상 매출할인
        "sec3": [],  # 저가보상 미결건
        "sec4": [],  # 약가인하 미결건
    }
    hospital_map: dict[str, tuple[str, str]] = {}  # 거래코드 -> (거래처약칭, 거래처정식명)
    vendor_map: dict[str, str] = {}                # 매입처코드 -> 매입처명
    months_found: set[str] = set()

    current_sec = "sec1"
    for r_idx, row in enumerate(rows):
        # 섹션 구분자 탐색
        joined = " ".join(str(x) for x in row if x is not None and str(x).strip() != "")
        if not joined:
            continue
        if "바슈헬스코리아" in joined and "※" in joined:
            current_sec = "sec2"
            continue
        elif "저가보상 미결건" in joined and "※" in joined:
            current_sec = "sec3"
            continue
        elif "약가인하 미결건" in joined and "※" in joined:
            current_sec = "sec4"
            continue

        c0 = clean_code(row[0] if len(row) > 0 else "")
        c2 = clean_code(row[2] if len(row) > 2 else "")
        if c0 == "코드" or "Q필터" in joined:
            continue
        if not c0 and not c2:
            continue

        # 패딩
        padded = list(row) + [""] * (26 - len(row))
        v_cd = clean_code(padded[2])
        v_nm = str(padded[3] or "").strip()
        c_cd = clean_code(padded[18])
        c_short = str(padded[16] or "").strip()
        c_full = str(padded[19] or "").strip()
        code = clean_code(padded[0]) or (v_cd + c_cd)

        if v_cd and v_nm:
            vendor_map[v_cd] = v_nm
        if c_cd and (c_short or c_full):
            hospital_map[c_cd] = (c_short or c_full, c_full or c_short)

        # 날짜/기준년월 추출
        m_date = parse_date_str(padded[1])
        ilja_raw = padded[9]
        if current_sec == "sec1":
            ym = parse_ym(ilja_raw) or parse_ym(m_date)
            ilja_disp = ym_to_yy_slash_mm(ym) if ym else str(ilja_raw or "").strip()
            if not m_date and ym:
                m_date = f"{ym}-01"
        else:
            ilja_disp = parse_date_str(ilja_raw)
            ym = parse_ym(ilja_disp)

        if ym:
            months_found.add(ym)

        bal_date = parse_date_str(padded[12])
        yejeong = clean_num(padded[11])
        geumaek = clean_num(padded[14])
        migyeol = clean_num(padded[15])
        # Sample.xls R42 처럼 수식/오타(23)로 들어간 미결금액 보정: 예정금액 - 금액
        if abs(migyeol - 23.0) < 1e-6 and yejeong > 1000:
            migyeol = yejeong - geumaek

        item: dict[str, Any] = {
            "_orig_row": r_idx + 1,
            "_section": current_sec,
            "_status": "기존",
            "_changes": {},
            "ym": ym,
            "코드": code,
            "매입월": m_date,
            "매입처": v_cd,
            "매입처명": v_nm,
            "조건": padded[4] if padded[4] not in (None, "") else "",
            "사전%": str(padded[5] or "").strip(),
            "매입%": str(padded[6] or "").strip(),
            "수금%": str(padded[7] or "").strip(),
            "년%": str(padded[8] or "").strip(),
            "일자": ilja_disp,
            "적요": str(padded[10] or "").strip(),
            "예정금액": yejeong,
            "발행일자": bal_date,
            "내용": str(padded[13] or "").strip(),
            "금액": geumaek,
            "미결금액": migyeol,
            "거래처": c_short,
            "비고": str(padded[17] or "").strip(),
            "거래코드": c_cd,
            "거래처명": c_full,
        }

        if current_sec == "sec1":
            item["자료비고"] = clean_num(padded[20]) if padded[20] not in (None, "") else ""
        elif current_sec == "sec3":
            item["참조"] = clean_num(padded[20]) if padded[20] not in (None, "") else yejeong
            item["참조-현 내역"] = clean_num(padded[21]) if padded[21] not in (None, "") else (migyeol if migyeol != 0 else -yejeong)
            item["예정 차"] = clean_num(padded[22]) if padded[22] not in (None, "") else (yejeong - geumaek * 2 if geumaek else -yejeong)
            item["미결 차"] = clean_num(padded[23]) if padded[23] not in (None, "") else 0.0
            item["잡행일"] = parse_date_str(padded[24]) if padded[24] not in (None, "", 0, 0.0) else ""
            wan = str(padded[25] or "").strip()
            if wan in ("0", "0.0"):
                wan = ""
            item["완결"] = wan
        elif current_sec == "sec4":
            item["공란1"] = ""
            item["공란2"] = ""
            item["공란3"] = ""
            item["오차분"] = clean_num(padded[23]) if padded[23] not in (None, "") else ""
            item["잡행일"] = parse_date_str(padded[24]) if padded[24] not in (None, "", 0, 0.0) else ""

        sections[current_sec].append(item)

    return {
        "sections": sections,
        "hospital_map": hospital_map,
        "vendor_map": vendor_map,
        "months": sorted(months_found),
        "counts": {k: len(v) for k, v in sections.items()},
    }


# ──────────────────────────────────────────────────────────────
# 2-1. 사후미결 (미결_병원경로_202511-202610.xlsx) 파서
# ──────────────────────────────────────────────────────────────
def parse_sahu_file(filepath: str | Path) -> dict[str, Any]:
    names = get_sheet_names(filepath)
    target_sheet = "미결 발생처" if "미결 발생처" in names else names[0]
    rows = read_sheet_rows(filepath, target_sheet)

    records: list[dict[str, Any]] = []
    months_found: set[str] = set()
    hospital_map: dict[str, tuple[str, str]] = {}
    vendor_map: dict[str, str] = {}

    header_idx = 0
    for i, r in enumerate(rows[:10]):
        vals = [str(x or "").strip() for x in r]
        if "매입처" in vals and "예정금액" in vals:
            header_idx = i
            break

    for r_idx in range(header_idx + 1, len(rows)):
        row = rows[r_idx]
        padded = list(row) + [None] * (18 - len(row))
        v_cd = clean_code(padded[0])
        v_nm = str(padded[1] or "").strip()
        if not v_cd or v_cd == "매입처" or "합계" in v_cd or "합계" in v_nm:
            continue

        c_cd = clean_code(padded[16])
        c_short = str(padded[14] or "").strip()
        c_full = str(padded[17] or "").strip() or c_short
        ilja_raw = str(padded[7] or "").strip()
        ym = parse_ym(ilja_raw)
        if ym:
            months_found.add(ym)

        if v_cd and v_nm:
            vendor_map[v_cd] = v_nm
        if c_cd and (c_short or c_full):
            hospital_map[c_cd] = (c_short or c_full, c_full or c_short)

        yejeong = clean_num(padded[9])
        bal_date = parse_date_str(padded[10])
        geumaek = clean_num(padded[12])
        migyeol = clean_num(padded[13])
        naeyong_raw = str(padded[11] or "").strip()
        jeokyo = str(padded[8] or "").strip()

        sajeon = "O" if str(padded[3] or "").strip() in ("○", "O", "o") else ""
        maeip = "O" if (str(padded[4] or "").strip() in ("○", "O", "o") or "매입할인" in naeyong_raw) else ""
        sugeum = "O" if (str(padded[5] or "").strip() in ("○", "O", "o") or "수금할인" in naeyong_raw) else ""
        nyeon = "O" if str(padded[6] or "").strip() in ("○", "O", "o") else ""

        # Sample.xls 규칙: 집행(발행일자 또는 금액)이 없는 미결 상태에서는 집행 '내용' 칸을 비워둠
        naeyong = naeyong_raw if (bal_date or geumaek != 0) else ""

        records.append({
            "_src_row": r_idx + 1,
            "_section": "sec1",
            "ym": ym,
            "코드": f"{v_cd}{c_cd}",
            "매입월": f"{ym}-01" if ym else "",
            "매입처": v_cd,
            "매입처명": v_nm,
            "조건": padded[2] if padded[2] not in (None, "") else "",
            "사전%": sajeon,
            "매입%": maeip,
            "수금%": sugeum,
            "년%": nyeon,
            "일자": ym_to_yy_slash_mm(ym) if ym else ilja_raw,
            "적요": jeokyo,
            "예정금액": yejeong,
            "발행일자": bal_date,
            "내용": naeyong,
            "금액": geumaek,
            "미결금액": migyeol,
            "거래처": c_short,
            "비고": str(padded[15] or "").strip(),
            "거래코드": c_cd,
            "거래처명": c_full,
            "자료비고": yejeong * 2 if yejeong else "",
        })

    return {
        "records": records,
        "months": sorted(months_found),
        "hospital_map": hospital_map,
        "vendor_map": vendor_map,
        "count": len(records),
    }


# ──────────────────────────────────────────────────────────────
# 2-2. 저가미결 (병원사후_미결_관리_26년_9월.xlsx) 파서
# ──────────────────────────────────────────────────────────────
def parse_jeoga_file(filepath: str | Path) -> dict[str, Any]:
    names = get_sheet_names(filepath)
    hospital_map: dict[str, tuple[str, str]] = {}
    vendor_map: dict[str, str] = {}

    # Sheet2 매핑 테이블 먼저 로드 (경로코드 -> 병원 정식명/약칭)
    if "Sheet2" in names:
        s2_rows = read_sheet_rows(filepath, "Sheet2")
        for r in s2_rows[1:]:
            if len(r) >= 5:
                v_cd = clean_code(r[0])
                v_nm = str(r[1] or "").strip()
                c_cd = clean_code(r[3])
                c_full = str(r[4] or "").strip()
                c_short = str(r[6] if len(r) > 6 and r[6] else c_full).strip()
                if v_cd and v_nm:
                    vendor_map[v_cd] = v_nm
                if c_cd and c_full:
                    hospital_map[c_cd] = (c_short or c_full, c_full)

    target_sheet = "Sheet1" if "Sheet1" in names else names[0]
    rows = read_sheet_rows(filepath, target_sheet)

    header_idx = 0
    for i, r in enumerate(rows[:10]):
        vals = [str(x or "").strip() for x in r]
        if "매입처" in vals and "예정금액" in vals:
            header_idx = i
            break

    records: list[dict[str, Any]] = []
    months_found: set[str] = set()

    for r_idx in range(header_idx + 1, len(rows)):
        row = rows[r_idx]
        padded = list(row) + [None] * (14 - len(row))
        v_cd = clean_code(padded[1])
        v_nm = str(padded[2] or "").strip()
        if not v_cd or v_cd == "매입처":
            continue

        c_cd = clean_code(padded[10])
        c_short = str(padded[9] or "").strip()
        c_full = hospital_map.get(c_cd, (c_short, c_short))[1] or c_short
        if v_cd and v_nm:
            vendor_map[v_cd] = v_nm
        if c_cd and c_short and c_cd not in hospital_map:
            hospital_map[c_cd] = (c_short, c_full)

        ilja_str = parse_date_str(padded[3])
        ym = parse_ym(ilja_str)
        if ym:
            months_found.add(ym)

        yejeong = clean_num(padded[4])
        bal_date = parse_date_str(padded[5])
        naeyong = str(padded[6] or "").strip()
        geumaek = clean_num(padded[7])
        migyeol = clean_num(padded[8])
        # 미결금액이 비어있거나 수식 미계산인 경우 보정
        if padded[8] is None and (yejeong != 0 or geumaek != 0):
            migyeol = yejeong - geumaek

        bigo_raw = str(padded[11] or "").strip()
        is_settled = (bigo_raw == "완") or (yejeong != 0 and abs(migyeol) < 1e-4 and geumaek != 0)
        wan_flag = "완" if is_settled else ""

        # Sample.xls 의 저가보상 일자 표기는 해당월 1일 (예: 2026-08-01, 2026-09-01), 비고는 'YY.MM.01 보상신청'
        ilja_norm = f"{ym}-01" if ym else ilja_str
        bigo_disp = f"{ym[2:4]}.{ym[5:7]}.01 보상신청" if ym else bigo_raw

        records.append({
            "_src_row": r_idx + 1,
            "_section": "sec3",
            "ym": ym,
            "코드": f"{v_cd}{c_cd}",
            "매입월": "",
            "매입처": v_cd,
            "매입처명": v_nm,
            "조건": "",
            "사전%": "",
            "매입%": "",
            "수금%": "",
            "년%": "",
            "일자": ilja_norm,
            "적요": "병원 저가 보상신청내역",
            "예정금액": yejeong,
            "발행일자": bal_date,
            "내용": naeyong,
            "금액": geumaek if geumaek != 0 or is_settled else "",
            "미결금액": migyeol,
            "거래처": c_short,
            "비고": bigo_disp,
            "거래코드": c_cd,
            "거래처명": c_full,
            "참조": yejeong,
            "참조-현 내역": -yejeong if is_settled else migyeol,
            "예정 차": yejeong if is_settled else -migyeol,
            "미결 차": 0.0,
            "잡행일": bal_date if is_settled else "",
            "완결": wan_flag,
        })

    return {
        "records": records,
        "months": sorted(months_found),
        "hospital_map": hospital_map,
        "vendor_map": vendor_map,
        "count": len(records),
    }


# ──────────────────────────────────────────────────────────────
# 2-3. 약가미결 (약가인하_미결_관리(병원부)S.xls) 파서
# ──────────────────────────────────────────────────────────────
def parse_yakga_file(filepath: str | Path) -> dict[str, Any]:
    names = get_sheet_names(filepath)
    hospital_map: dict[str, tuple[str, str]] = {}
    vendor_map: dict[str, str] = {}

    # Sheet1 에 매입경로 코드 및 매입경로명 매핑이 존재함
    if "Sheet1" in names:
        s1_rows = read_sheet_rows(filepath, "Sheet1")
        for r in s1_rows[1:]:
            if len(r) >= 5:
                c_cd = clean_code(r[1])
                c_full = str(r[2] or "").strip()
                v_cd = clean_code(r[3])
                v_nm = str(r[4] or "").strip()
                if c_cd and c_full:
                    hospital_map[c_cd] = (c_full, c_full)
                if v_cd and v_nm:
                    vendor_map[v_cd] = v_nm

    target_sheet = "약가인하" if "약가인하" in names else names[0]
    rows = read_sheet_rows(filepath, target_sheet)

    header_idx = 0
    for i, r in enumerate(rows[:10]):
        vals = [str(x or "").strip() for x in r]
        if "매입처" in vals and "예정금액" in vals:
            header_idx = i
            break

    records: list[dict[str, Any]] = []
    months_found: set[str] = set()

    for r_idx in range(header_idx + 1, len(rows)):
        row = rows[r_idx]
        padded = list(row) + [""] * (22 - len(row))
        code_raw = clean_code(padded[0])
        v_cd = clean_code(padded[2])
        v_nm = str(padded[3] or "").strip()
        if not v_cd or v_cd == "매입처":
            continue

        # 거래코드는 18번 컬럼 또는 20번 컬럼, 없으면 코드에서 매입처코드 뒤쪽 추출
        c_cd = clean_code(padded[18]) or clean_code(padded[20])
        if not c_cd and code_raw.startswith(v_cd) and len(code_raw) > len(v_cd):
            c_cd = code_raw[len(v_cd):]

        c_short = str(padded[16] or "").strip() or "병원부"
        c_full = str(padded[19] or "").strip()
        if not c_full and c_cd in hospital_map:
            c_full = hospital_map[c_cd][1]

        if v_cd and v_nm:
            vendor_map[v_cd] = v_nm
        if c_cd and c_full:
            hospital_map[c_cd] = (c_short, c_full)

        ilja_str = parse_date_str(padded[9])
        ym = parse_ym(ilja_str)
        if ym:
            months_found.add(ym)

        yejeong = clean_num(padded[11])
        bal_date = parse_date_str(padded[12])
        naeyong = str(padded[13] or "").strip()
        geumaek = clean_num(padded[14])
        migyeol = clean_num(padded[15])

        records.append({
            "_src_row": r_idx + 1,
            "_section": "sec4",
            "ym": ym,
            "코드": code_raw or f"{v_cd}{c_cd}",
            "매입월": parse_date_str(padded[1]),
            "매입처": v_cd,
            "매입처명": v_nm,
            "조건": padded[4] if padded[4] not in (None, "") else "",
            "사전%": str(padded[5] or "").strip(),
            "매입%": str(padded[6] or "").strip(),
            "수금%": str(padded[7] or "").strip(),
            "년%": str(padded[8] or "").strip(),
            "일자": ilja_str,
            "적요": str(padded[10] or "").strip() or "병원 약가인하 보상신청내역",
            "예정금액": yejeong,
            "발행일자": bal_date,
            "내용": naeyong,
            "금액": geumaek if (geumaek != 0 or bal_date) else "",
            "미결금액": migyeol,
            "거래처": c_short,
            "비고": str(padded[17] or "").strip(),
            "거래코드": c_cd,
            "거래처명": c_full,
            "공란1": "",
            "공란2": "",
            "공란3": "",
            "오차분": "",
            "잡행일": bal_date if (abs(migyeol) < 1.0 and geumaek > 0) else "",
        })

    return {
        "records": records,
        "months": sorted(months_found),
        "hospital_map": hospital_map,
        "vendor_map": vendor_map,
        "count": len(records),
    }


# ──────────────────────────────────────────────────────────────
# 4. 비교·수정·신규 통합 및 매입처별 요약 리포트 엔진
# ──────────────────────────────────────────────────────────────
def analyze_and_merge(
    orig_data: dict[str, Any],
    sahu_data: dict[str, Any],
    jeoga_data: dict[str, Any],
    yakga_data: dict[str, Any],
    base_month: str = "2026-09",
    vendor_scope: str = "all",          # "all" (전체 매입처) | "sample_only" (원본 매입처만)
    include_prior_unsettled: bool = False,  # True 면 기준월 이전 미결건도 신규로 모두 포함
) -> dict[str, Any]:
    """
    2번(원본 Sample.xls)과 3번(3종 데이터)을 비교하여:
    - 기존 행: 3종의 최신 상태(발행일자, 내용, 금액, 미결금액, 완결여부 등)로 업데이트 (완결된 건도 유지)
    - 신규 행: 선택한 생성 기준월(base_month)에 해당하는 신규 데이터를 추가
    - 매입처별 요약 리포트(vendor_summary) 및 4대 섹션 통합 결과 반환
    """
    # 통합 병원명/매입처명 사전 구축
    hosp_map: dict[str, tuple[str, str]] = {}
    for d in (yakga_data, jeoga_data, sahu_data, orig_data):
        hosp_map.update(d.get("hospital_map", {}))

    vend_map: dict[str, str] = {}
    for d in (yakga_data, jeoga_data, sahu_data, orig_data):
        vend_map.update(d.get("vendor_map", {}))

    orig_vendors = set(orig_data.get("vendor_map", {}).keys())

    def enrich_names(row: dict[str, Any]) -> dict[str, Any]:
        c_cd = row.get("거래코드", "")
        if c_cd in hosp_map:
            short_nm, full_nm = hosp_map[c_cd]
            if not row.get("거래처"):
                row["거래처"] = short_nm
            if not row.get("거래처명"):
                row["거래처명"] = full_nm
        v_cd = row.get("매입처", "")
        if v_cd in vend_map and not row.get("매입처명"):
            row["매입처명"] = vend_map[v_cd]
        return row

    def merge_section(
        sec_key: str,
        orig_rows: list[dict[str, Any]],
        new_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        used_src_rows: set[int] = set()

        # 1) 기존 원본 행 매칭 및 수정 반영
        for orig in orig_rows:
            item = dict(orig)
            item["_changes"] = {}
            enrich_names(item)

            v_cd = item["매입처"]
            c_cd = item["거래코드"]
            code = item["코드"]
            ym = item["ym"]
            yejeong = clean_num(item["예정금액"])

            # 후보 탐색: (매입처, 거래코드, 년월) 또는 (코드, 년월)
            candidates = [
                r for r in new_rows
                if r["_src_row"] not in used_src_rows
                and r["ym"] == ym
                and ((r["매입처"] == v_cd and r["거래코드"] == c_cd) or r["코드"] == code)
            ]
            # 후보가 여러 개면 예정금액이 가장 가까운 행 우선
            match = None
            if candidates:
                candidates.sort(key=lambda r: abs(clean_num(r["예정금액"]) - yejeong))
                match = candidates[0]
                used_src_rows.add(match["_src_row"])

            if match:
                # 변경 비교 대상 필드
                compare_fields = ["예정금액", "발행일자", "내용", "금액", "미결금액"]
                if sec_key == "sec3":
                    compare_fields.append("완결")

                changed = False
                for f in compare_fields:
                    old_val = item.get(f, "")
                    new_val = match.get(f, "")
                    if f in ("예정금액", "금액", "미결금액"):
                        if abs(clean_num(old_val) - clean_num(new_val)) >= 1.0:
                            item["_changes"][f] = {"old": clean_num(old_val), "new": clean_num(new_val)}
                            item[f] = new_val
                            changed = True
                    else:
                        s_old = str(old_val or "").strip()
                        s_new = str(new_val or "").strip()
                        if s_new and s_old != s_new:
                            item["_changes"][f] = {"old": s_old, "new": s_new}
                            item[f] = s_new
                            changed = True

                # 부가 파생 컬럼 동기화
                if sec_key == "sec3":
                    for aux in ("참조", "참조-현 내역", "예정 차", "미결 차", "잡행일", "완결"):
                        if match.get(aux) not in (None, ""):
                            item[aux] = match[aux]
                elif sec_key == "sec4":
                    if match.get("잡행일"):
                        item["잡행일"] = match["잡행일"]

                is_now_settled = (
                    (sec_key == "sec3" and item.get("완결") == "완")
                    or (clean_num(item.get("예정금액")) != 0 and abs(clean_num(item.get("미결금액"))) < 1.0 and clean_num(item.get("금액")) != 0)
                )
                if changed:
                    item["_status"] = "완결" if is_now_settled else "수정"
                else:
                    item["_status"] = "완결" if is_now_settled else "기존"
            else:
                is_now_settled = (
                    (sec_key == "sec3" and item.get("완결") == "완")
                    or (clean_num(item.get("예정금액")) != 0 and abs(clean_num(item.get("미결금액"))) < 1.0 and clean_num(item.get("금액")) != 0)
                )
                item["_status"] = "완결" if is_now_settled else "기존"

            merged.append(item)

        # 2) 3종 파일에서 신규 행 추가
        base_year = base_month[:4] if len(base_month) >= 4 else "2026"
        for r in new_rows:
            if r["_src_row"] in used_src_rows:
                continue
            if vendor_scope == "sample_only" and r["매입처"] not in orig_vendors:
                continue

            r_ym = r["ym"]
            migyeol = clean_num(r["미결금액"])
            yejeong = clean_num(r["예정금액"])

            should_add = False
            if sec_key in ("sec1", "sec3"):
                if r_ym == base_month:
                    # 기초금액(25/10)이 아닌 실제 발생/집행 건이거나 미결이 있는 건
                    if yejeong != 0 or migyeol != 0 or clean_num(r["금액"]) != 0:
                        should_add = True
                elif include_prior_unsettled and r_ym and r_ym <= base_month:
                    if sec_key == "sec3":
                        if r.get("완결") != "완" and abs(migyeol) >= 1.0:
                            should_add = True
                    else:
                        if abs(migyeol) >= 1.0 and "기초" not in str(r.get("내용", "")):
                            should_add = True
            elif sec_key == "sec4":
                # 약가인하는 연초/특정월(예: 2026-01 '26.01.01 인하분' 124건) 일괄 발생하므로:
                # 1) 기준년도(예: 2026년) 내 기준월 이하의 약가인하 내역 전체 반영 (완결 포함 유지 규칙과 일관)
                # 2) 또는 이전 연도 중 미결잔액(abs(migyeol) >= 1) 보유 건 반영
                if r_ym and r_ym <= base_month:
                    if r_ym.startswith(base_year) or abs(migyeol) >= 1.0:
                        should_add = True

            if should_add:
                new_item = dict(r)
                enrich_names(new_item)
                is_settled = (
                    (sec_key == "sec3" and new_item.get("완결") == "완")
                    or (yejeong != 0 and abs(migyeol) < 1.0 and clean_num(new_item.get("금액")) != 0)
                )
                new_item["_status"] = "완결" if is_settled else "신규"
                new_item["_changes"] = {}
                merged.append(new_item)

        return merged

    sec1_merged = merge_section("sec1", orig_data["sections"]["sec1"], sahu_data["records"])
    sec2_merged = [enrich_names(dict(r, _status="기존", _changes={})) for r in orig_data["sections"]["sec2"]]
    sec3_merged = merge_section("sec3", orig_data["sections"]["sec3"], jeoga_data["records"])
    sec4_merged = merge_section("sec4", orig_data["sections"]["sec4"], yakga_data["records"])

    sections_merged = {
        "sec1": sec1_merged,
        "sec2": sec2_merged,
        "sec3": sec3_merged,
        "sec4": sec4_merged,
    }

    # 3) 매입처별 요약 리포트 집계
    vendor_agg: dict[str, dict[str, Any]] = {}
    section_labels = {
        "sec1": "사후미결",
        "sec2": "바슈헬스",
        "sec3": "저가미결",
        "sec4": "약가미결",
    }

    total_yejeong = 0.0
    total_geumaek = 0.0
    total_migyeol = 0.0
    status_counts = {"기존": 0, "수정": 0, "신규": 0, "완결": 0}

    for sec_key, rows in sections_merged.items():
        for r in rows:
            v_cd = r.get("매입처") or "미상"
            v_nm = r.get("매입처명") or vend_map.get(v_cd, v_cd)
            if v_cd not in vendor_agg:
                vendor_agg[v_cd] = {
                    "매입처코드": v_cd,
                    "매입처명": v_nm,
                    "사후_예정": 0.0, "사후_집행": 0.0, "사후_미결": 0.0, "사후_건수": 0,
                    "바슈_예정": 0.0, "바슈_집행": 0.0, "바슈_미결": 0.0, "바슈_건수": 0,
                    "저가_예정": 0.0, "저가_집행": 0.0, "저가_미결": 0.0, "저가_건수": 0,
                    "약가_예정": 0.0, "약가_집행": 0.0, "약가_미결": 0.0, "약가_건수": 0,
                    "총_예정금액": 0.0,
                    "총_집행금액": 0.0,
                    "총_미결금액": 0.0,
                    "총_건수": 0,
                    "기존_건수": 0,
                    "수정_건수": 0,
                    "신규_건수": 0,
                    "완결_건수": 0,
                }
            va = vendor_agg[v_cd]
            yj = clean_num(r.get("예정금액"))
            gm = clean_num(r.get("금액"))
            mg = clean_num(r.get("미결금액"))
            st = r.get("_status", "기존")

            prefix = {"sec1": "사후", "sec2": "바슈", "sec3": "저가", "sec4": "약가"}[sec_key]
            va[f"{prefix}_예정"] += yj
            va[f"{prefix}_집행"] += gm
            va[f"{prefix}_미결"] += mg
            va[f"{prefix}_건수"] += 1

            va["총_예정금액"] += yj
            va["총_집행금액"] += gm
            va["총_미결금액"] += mg
            va["총_건수"] += 1

            if st in ("기존", "수정", "신규", "완결"):
                va[f"{st}_건수"] += 1
                status_counts[st] += 1

            total_yejeong += yj
            total_geumaek += gm
            total_migyeol += mg

    vendor_summary = sorted(
        vendor_agg.values(),
        key=lambda x: (abs(x["총_미결금액"]), x["총_예정금액"]),
        reverse=True,
    )

    section_summary = {}
    for sec_key, rows in sections_merged.items():
        section_summary[sec_key] = {
            "label": section_labels[sec_key],
            "count": len(rows),
            "예정금액": sum(clean_num(r.get("예정금액")) for r in rows),
            "집행금액": sum(clean_num(r.get("금액")) for r in rows),
            "미결금액": sum(clean_num(r.get("미결금액")) for r in rows),
            "신규": sum(1 for r in rows if r.get("_status") == "신규"),
            "수정": sum(1 for r in rows if r.get("_status") == "수정"),
            "완결": sum(1 for r in rows if r.get("_status") == "완결"),
            "기존": sum(1 for r in rows if r.get("_status") == "기존"),
        }

    return {
        "base_month": base_month,
        "vendor_scope": vendor_scope,
        "include_prior_unsettled": include_prior_unsettled,
        "kpis": {
            "총_예정금액": total_yejeong,
            "총_집행금액": total_geumaek,
            "총_미결금액": total_migyeol,
            "총_건수": sum(len(v) for v in sections_merged.values()),
            "매입처_수": len(vendor_summary),
            "상태별_건수": status_counts,
        },
        "section_summary": section_summary,
        "vendor_summary": vendor_summary,
        "sections": sections_merged,
    }


# ──────────────────────────────────────────────────────────────
# 5. 엑셀 생성 엔진 (2번 Sample.xls 4섹션 구조 유지 + 디자인 재구성)
# ──────────────────────────────────────────────────────────────
def generate_integrated_excel(analysis_result: dict[str, Any], output_path: str | Path) -> str:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "미결(병원부)"
    ws.views.sheetView[0].showGridLines = True

    # Clinical Ledger Precision 디자인 토큰
    f_title = Font(name="맑은 고딕", size=11, bold=True, color="FFFFFF")
    f_sec_banner = Font(name="맑은 고딕", size=10, bold=True, color="1E3A8A")
    f_th = Font(name="맑은 고딕", size=9, bold=True, color="1E293B")
    f_td = Font(name="맑은 고딕", size=9, color="0F172A")
    f_td_num = Font(name="맑은 고딕", size=9, color="0F172A")
    f_td_neg = Font(name="맑은 고딕", size=9, bold=True, color="DC2626")
    f_td_settled = Font(name="맑은 고딕", size=9, bold=True, color="059669")
    f_td_mod = Font(name="맑은 고딕", size=9, bold=True, color="B45309")

    fill_top_bar = PatternFill("solid", fgColor="1E3A8A")      # Deep Cobalt Navy
    fill_sec_banner = PatternFill("solid", fgColor="EFF6FF")   # Soft Cobalt Wash
    fill_th = PatternFill("solid", fgColor="F1F5F9")           # Slate 100 Header
    fill_zebra = PatternFill("solid", fgColor="F8FAFC")        # Slate 50 Zebra
    fill_white = PatternFill("solid", fgColor="FFFFFF")
    fill_new = PatternFill("solid", fgColor="EFF6FF")          # 신규 행 하이라이트
    fill_mod = PatternFill("solid", fgColor="FFFBEB")          # 수정 행 하이라이트
    fill_settled = PatternFill("solid", fgColor="ECFDF5")      # 완결 행 하이라이트

    thin_border_side = Side(style="thin", color="CBD5E1")
    med_navy_side = Side(style="medium", color="1E3A8A")
    double_bottom_side = Side(style="double", color="475569")

    b_data = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    b_th = Border(left=thin_border_side, right=thin_border_side, top=med_navy_side, bottom=double_bottom_side)
    b_banner = Border(left=med_navy_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

    align_center = Alignment(horizontal="center", vertical="center", wrap_text=False)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=False)
    align_right = Alignment(horizontal="right", vertical="center", wrap_text=False)

    num_fmt_krw = "#,##0;[Red]-#,##0;\"-\""

    sections = analysis_result["sections"]
    base_month = analysis_result.get("base_month", "")

    # ── Row 1: 상단 요약 컨트롤 바 (Sample.xls R1 구조 호환 + 디자인 재구성)
    ws.row_dimensions[1].height = 28
    for c in range(1, 27):
        cell = ws.cell(1, c, "")
        cell.fill = fill_top_bar
        cell.font = f_title
        cell.alignment = align_center

    ws.cell(1, 3, f"Q필터 : 기준월 [{base_month}]")
    ws.cell(1, 6, "정")
    ws.cell(1, 8, "책")
    ws.cell(1, 11, "범례: 확정 / 예외추가% / 신규(청색) / 수정(황색) / 완결(녹색)")
    ws.cell(1, 13, "집   행        미결금액:")
    # P1(16열)에 전체 미결금액 SUBTOTAL 수식 배치 (Sample.xls 동일 위치)
    ws.cell(1, 18, "※ 수금할인&할인조정 미결누적 관리 (통합 리포트)")
    ws.cell(1, 18).alignment = align_left

    curr_row = 2

    def write_header_row(row_idx: int, cols: list[str]):
        ws.row_dimensions[row_idx].height = 24
        for c_idx, col_name in enumerate(cols, start=1):
            label = "" if col_name.startswith("공란") else col_name
            cell = ws.cell(row_idx, c_idx, label)
            cell.font = f_th
            cell.fill = fill_th
            cell.border = b_th
            cell.alignment = align_center

    def write_data_rows(start_row: int, rows: list[dict[str, Any]], cols: list[str]) -> int:
        r_cursor = start_row
        for idx, r in enumerate(rows):
            ws.row_dimensions[r_cursor].height = 20
            st = r.get("_status", "기존")
            if st == "신규":
                row_fill = fill_new
            elif st == "수정":
                row_fill = fill_mod
            elif st == "완결":
                row_fill = fill_settled
            else:
                row_fill = fill_zebra if idx % 2 == 1 else fill_white

            for c_idx, col_name in enumerate(cols, start=1):
                val = r.get(col_name, "")
                if col_name.startswith("공란"):
                    val = ""
                cell = ws.cell(r_cursor, c_idx)
                cell.fill = row_fill
                cell.border = b_data

                if col_name in ("예정금액", "금액", "미결금액", "자료비고", "참조", "참조-현 내역", "예정 차", "미결 차", "오차분"):
                    if val == "" or val is None:
                        cell.value = None
                    else:
                        num_v = clean_num(val)
                        cell.value = num_v
                        cell.number_format = num_fmt_krw
                        cell.font = f_td_neg if num_v < 0 else (f_td_mod if col_name in r.get("_changes", {}) else f_td_num)
                    cell.alignment = align_right
                elif col_name == "조건":
                    if isinstance(val, (int, float)) and val != 0:
                        cell.value = float(val)
                        cell.number_format = "0.0%"
                    else:
                        cell.value = str(val or "")
                    cell.font = f_td
                    cell.alignment = align_center
                elif col_name in ("코드", "매입월", "매입처", "사전%", "매입%", "수금%", "년%", "일자", "발행일자", "거래코드", "잡행일", "완결"):
                    cell.value = str(val or "")
                    cell.font = f_td_settled if (col_name == "완결" and val == "완") else f_td
                    cell.alignment = align_center
                else:
                    cell.value = str(val or "")
                    cell.font = f_td
                    cell.alignment = align_left

            r_cursor += 1
        return r_cursor

    def write_section_banner(row_idx: int, title: str, max_cols: int):
        ws.row_dimensions[row_idx].height = 24
        for c in range(1, max_cols + 1):
            cell = ws.cell(row_idx, c, "")
            cell.fill = fill_sec_banner
            cell.border = b_banner
        title_cell = ws.cell(row_idx, 3, title)
        title_cell.font = f_sec_banner
        title_cell.alignment = align_left

    # ── 섹션 1: 정책 / 사후·수금할인 미결
    write_header_row(curr_row, SEC1_COLS)
    curr_row += 1
    curr_row = write_data_rows(curr_row, sections["sec1"], SEC1_COLS)

    # 빈 줄 (Sample.xls 구조와 동일하게 1행 공백)
    curr_row += 1

    # ── 섹션 2: ※ 바슈헬스코리아(솔타) 예상 매출할인
    write_section_banner(curr_row, "※ 바슈헬스코리아(솔타) 예상 매출할인", len(SEC2_COLS))
    curr_row += 1
    write_header_row(curr_row, SEC2_COLS)
    curr_row += 1
    curr_row = write_data_rows(curr_row, sections["sec2"], SEC2_COLS)

    curr_row += 1

    # ── 섹션 3: ※ 저가보상 미결건
    write_section_banner(curr_row, "※ 저가보상 미결건", len(SEC3_COLS))
    curr_row += 1
    write_header_row(curr_row, SEC3_COLS)
    curr_row += 1
    curr_row = write_data_rows(curr_row, sections["sec3"], SEC3_COLS)

    curr_row += 1

    # ── 섹션 4: ※ 약가인하 미결건
    write_section_banner(curr_row, "※ 약가인하 미결건", len(SEC4_COLS))
    curr_row += 1
    write_header_row(curr_row, SEC4_COLS)
    curr_row += 1
    curr_row = write_data_rows(curr_row, sections["sec4"], SEC4_COLS)

    # 상단 P1(16열)에 전체 미결금액 SUBTOTAL 수식 입력
    last_row = max(curr_row - 1, 3)
    p1 = ws.cell(1, 16, f"=SUBTOTAL(9,P3:P{last_row})")
    p1.font = Font(name="맑은 고딕", size=11, bold=True, color="FDE047")
    p1.fill = fill_top_bar
    p1.number_format = num_fmt_krw
    p1.alignment = align_right

    # 컬럼 너비 최적화
    col_widths = {
        1: 14, 2: 12, 3: 10, 4: 22, 5: 8,
        6: 7, 7: 7, 8: 7, 9: 7, 10: 12,
        11: 24, 12: 15, 13: 12, 14: 16, 15: 15,
        16: 16, 17: 16, 18: 20, 19: 10, 20: 28,
        21: 14, 22: 14, 23: 14, 24: 12, 25: 12, 26: 8,
    }
    for c_idx, w in col_widths.items():
        ws.column_dimensions[get_column_letter(c_idx)].width = w

    ws.freeze_panes = "A3"

    # ══════════════════════════════════════════════════════════
    # Sheet 2: 매입처별 요약 리포트 (부속 요약 시트)
    # ══════════════════════════════════════════════════════════
    ws_sum = wb.create_sheet(title="매입처별 요약 리포트")
    ws_sum.views.sheetView[0].showGridLines = True

    ws_sum.row_dimensions[1].height = 30
    for c in range(1, 16):
        cell = ws_sum.cell(1, c, "")
        cell.fill = fill_top_bar
        cell.font = f_title
    ws_sum.cell(1, 1, f"📊 매입처별 미결 통합 요약 리포트 (생성 기준월: {base_month})").alignment = align_left

    sum_headers = [
        "매입처코드", "매입처명",
        "사후미결(예정)", "사후미결(집행)", "사후미결(잔액)",
        "저가미결(예정)", "저가미결(집행)", "저가미결(잔액)",
        "약가미결(예정)", "약가미결(집행)", "약가미결(잔액)",
        "총 예정금액", "총 집행금액", "총 미결잔액",
        "변동내역(신규/수정/완결)"
    ]
    ws_sum.row_dimensions[2].height = 24
    for c_idx, h_text in enumerate(sum_headers, start=1):
        c = ws_sum.cell(2, c_idx, h_text)
        c.font = f_th
        c.fill = fill_th
        c.border = b_th
        c.alignment = align_center

    for i, v in enumerate(analysis_result["vendor_summary"], start=3):
        ws_sum.row_dimensions[i].height = 20
        r_fill = fill_zebra if i % 2 == 1 else fill_white
        row_vals = [
            v["매입처코드"], v["매입처명"],
            v["사후_예정"], v["사후_집행"], v["사후_미결"],
            v["저가_예정"], v["저가_집행"], v["저가_미결"],
            v["약가_예정"], v["약가_집행"], v["약가_미결"],
            v["총_예정금액"], v["총_집행금액"], v["총_미결금액"],
            f"신규 {v['신규_건수']} / 수정 {v['수정_건수']} / 완결 {v['완결_건수']}"
        ]
        for c_idx, val in enumerate(row_vals, start=1):
            c = ws_sum.cell(i, c_idx, val)
            c.fill = r_fill
            c.border = b_data
            if 3 <= c_idx <= 14:
                c.number_format = num_fmt_krw
                c.alignment = align_right
                c.font = f_td_neg if clean_num(val) < 0 else f_td_num
            elif c_idx in (1, 15):
                c.alignment = align_center
                c.font = f_td
            else:
                c.alignment = align_left
                c.font = f_td

    sum_widths = [12, 24, 15, 15, 15, 15, 15, 15, 15, 15, 15, 16, 16, 16, 22]
    for c_idx, w in enumerate(sum_widths, start=1):
        ws_sum.column_dimensions[get_column_letter(c_idx)].width = w
    ws_sum.freeze_panes = "C3"

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out_p))
    return str(out_p)
