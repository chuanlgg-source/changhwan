"""
reconcile_engine.py — 병원부 미결 통합 관리 및 리포트 엔진
1. 생성 기준월 선택
2. 원본데이터 로드 (4대 항목 구조 파싱: 사후미결, 사후미결(바슈), 저가미결, 약가미결)
3. 수정 및 신규데이터 3종 로드:
   - 3-1. 사후미결
   - 3-2. 저가미결
   - 3-3. 약가미결
4. 생성데이터 목표:
   - (1) 기준월 이전건: 스텝2 원본을 스텝 3-1 ~ 3-3 값으로 업데이트하되, 수정된 사항을 정리하여 항목별 리포트
   - (2) 기준월 해당건: 스텝2 원본에 스텝 3-1 ~ 3-3의 기준월 해당건 값을 추가
   - (3) 최종검증 방법: 스텝 3-1 ~ 3-3 각 항의 합계와 통합자료 각 항의 합계 일치 여부를 점검·검증
5. 업데이트된 엑셀파일 생성 (각 항목 타이틀 초기화 및 명칭 부여: 사후미결, 사후미결(바슈), 저가미결, 약가미결)
"""
from __future__ import annotations

import datetime
import math
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
    if not s or s in ("0", "0.0"):
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
# 섹션별 표준 명칭 및 컬럼 정의
# (최좌측 '코드' 삭제, 최우측 '자료비고' 삭제 반영)
# ──────────────────────────────────────────────────────────────
SECTION_TITLES = {
    "sec1": "사후미결",
    "sec2": "사후미결(바슈)",
    "sec3": "저가미결",
    "sec4": "약가미결",
}

COMMON_COLS = [
    "매입월", "매입처", "매입처명", "조건",
    "사전%", "매입%", "수금%", "년%", "일자",
    "적요", "예정금액", "발행일자", "내용", "금액",
    "미결금액", "거래처", "비고", "거래코드", "거래처명"
]

SEC1_COLS = COMMON_COLS
SEC2_COLS = COMMON_COLS
SEC3_COLS = COMMON_COLS + ["참조", "참조-현 내역", "예정 차", "미결 차", "잡행일", "완결"]
SEC4_COLS = COMMON_COLS + ["공란1", "공란2", "공란3", "오차분", "잡행일"]


# ──────────────────────────────────────────────────────────────
# 1. 스텝 2 원본 데이터 파서 (기존 양식 및 신규 생성 양식 모두 호환)
# ──────────────────────────────────────────────────────────────
def parse_original_sample(filepath: str | Path) -> dict[str, Any]:
    rows = read_sheet_rows(filepath, 0)
    sections: dict[str, list[dict[str, Any]]] = {
        "sec1": [],  # 사후미결
        "sec2": [],  # 사후미결(바슈)
        "sec3": [],  # 저가미결
        "sec4": [],  # 약가미결
    }
    hospital_map: dict[str, tuple[str, str]] = {}  # 거래코드 -> (거래처약칭, 거래처정식명)
    vendor_map: dict[str, str] = {}                # 매입처코드 -> 매입처명
    months_found: set[str] = set()

    current_sec = "sec1"
    has_code_col = True  # 기존 Sample.xls는 0열이 '코드', 신규 생성 통합파일은 0열이 '매입월'

    for r_idx, row in enumerate(rows):
        non_empty = [str(x).strip() for x in row if x is not None and str(x).strip() != ""]
        if not non_empty:
            continue
        joined = " ".join(non_empty)

        # 섹션 타이틀 행 판별 (신규 타이틀 및 기존 타이틀 모두 인식)
        first_cell = str(row[0] or "").strip() if len(row) > 0 else ""
        if len(non_empty) == 1 and first_cell in ("사후미결", "사후미결(바슈)", "저가미결", "약가미결"):
            if first_cell == "사후미결":
                current_sec = "sec1"
            elif first_cell == "사후미결(바슈)":
                current_sec = "sec2"
            elif first_cell == "저가미결":
                current_sec = "sec3"
            elif first_cell == "약가미결":
                current_sec = "sec4"
            continue

        if "사후미결(바슈)" in joined or ("바슈헬스코리아" in joined and "※" in joined):
            current_sec = "sec2"
            continue
        elif ("저가보상 미결건" in joined and "※" in joined) or (len(non_empty) <= 2 and first_cell == "저가미결"):
            current_sec = "sec3"
            continue
        elif ("약가인하 미결건" in joined and "※" in joined) or (len(non_empty) <= 2 and first_cell == "약가미결"):
            current_sec = "sec4"
            continue
        elif len(non_empty) <= 2 and first_cell == "사후미결":
            current_sec = "sec1"
            continue

        # 상단 요약줄 / 헤더 행 판별
        if "Q필터" in joined or "수금할인&할인조정" in joined:
            continue

        c0_str = str(row[0] or "").strip() if len(row) > 0 else ""
        c1_str = str(row[1] or "").strip() if len(row) > 1 else ""
        if c0_str == "코드" and c1_str == "매입월":
            has_code_col = True
            continue
        if c0_str == "매입월" and c1_str == "매입처":
            has_code_col = False
            continue

        # 컬럼 위치 정렬 (코드 컬럼이 없는 신규 양식이면 앞에 빈 요소를 붙여 인덱스 통일)
        aligned_row = list(row) if has_code_col else ([""] + list(row))
        padded = aligned_row + [""] * (26 - len(aligned_row))

        c0 = clean_code(padded[0])
        v_cd = clean_code(padded[2])
        if not c0 and not v_cd:
            continue

        v_nm = str(padded[3] or "").strip()
        c_cd = clean_code(padded[18])
        c_short = str(padded[16] or "").strip()
        c_full = str(padded[19] or "").strip()
        code = c0 or f"{v_cd}{c_cd}"

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
            ym = parse_ym(ilja_disp) or parse_ym(m_date)

        if ym:
            months_found.add(ym)

        bal_date = parse_date_str(padded[12])
        yejeong = clean_num(padded[11])
        geumaek = clean_num(padded[14])
        migyeol = clean_num(padded[15])

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

        if current_sec == "sec3":
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
# 3-1. 사후미결 파서
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

        # 집행(발행일자 또는 금액)이 없는 미결 상태에서는 집행 '내용' 칸을 비워둠
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
        })

    return {
        "records": records,
        "months": sorted(months_found),
        "hospital_map": hospital_map,
        "vendor_map": vendor_map,
        "count": len(records),
    }


# ──────────────────────────────────────────────────────────────
# 3-2. 저가미결 파서
# ──────────────────────────────────────────────────────────────
def parse_jeoga_file(filepath: str | Path) -> dict[str, Any]:
    names = get_sheet_names(filepath)
    hospital_map: dict[str, tuple[str, str]] = {}
    vendor_map: dict[str, str] = {}

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
        if padded[8] is None and (yejeong != 0 or geumaek != 0):
            migyeol = yejeong - geumaek

        bigo_raw = str(padded[11] or "").strip()
        is_settled = (bigo_raw == "완") or (yejeong != 0 and abs(migyeol) < 1e-4 and geumaek != 0)
        wan_flag = "완" if is_settled else ""

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
# 3-3. 약가미결 파서
# ──────────────────────────────────────────────────────────────
def parse_yakga_file(filepath: str | Path) -> dict[str, Any]:
    names = get_sheet_names(filepath)
    hospital_map: dict[str, tuple[str, str]] = {}
    vendor_map: dict[str, str] = {}

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
# 4. 생성데이터 통합 · 수정 리포트 · 최종검증 엔진
# ──────────────────────────────────────────────────────────────
def analyze_and_merge(
    orig_data: dict[str, Any],
    sahu_data: dict[str, Any],
    jeoga_data: dict[str, Any],
    yakga_data: dict[str, Any],
    base_month: str = "2026-09",
    vendor_scope: str = "all",
    include_prior_unsettled: bool = False,
) -> dict[str, Any]:
    """
    생성데이터 목표:
    1. 기준월 이전건 (ym < base_month):
       - 스텝2 원본을 스텝 3-1 ~ 3-3 값으로 업데이트하되, 수정된 사항을 정리하여 항목별 리포트한다.
    2. 기준월 해당건 (ym == base_month):
       - 스텝2 원본에 스텝 3-1 ~ 3-3의 기준월 해당건 값을 추가한다.
       (스텝2 원본에 이미 기준월 해당건이 일부 존재하는 경우 중복 없이 업데이트 후 나머지 기준월 해당건을 추가)
    3. 최종검증 방법:
       - 스텝 3-1 ~ 3-3 각 항의 합계는 통합자료의 각 항의 합과 일치 여부를 점검하여 검증한다.
    """
    hosp_map: dict[str, tuple[str, str]] = {}
    for d in (yakga_data, jeoga_data, sahu_data, orig_data):
        hosp_map.update(d.get("hospital_map", {}))

    vend_map: dict[str, str] = {}
    for d in (yakga_data, jeoga_data, sahu_data, orig_data):
        vend_map.update(d.get("vendor_map", {}))

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

    modified_by_section: dict[str, list[dict[str, Any]]] = {
        "sec1": [],
        "sec2": [],
        "sec3": [],
        "sec4": [],
    }
    modified_all: list[dict[str, Any]] = []
    verification_report: list[dict[str, Any]] = []

    def merge_section(
        sec_key: str,
        step_label: str,
        orig_rows: list[dict[str, Any]],
        new_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        used_src_rows: set[int] = set()
        matched_step3_rows: list[dict[str, Any]] = []
        unmatched_orig_rows: list[dict[str, Any]] = []

        # ── 1) 스텝2 원본 행(기준월 이전건 포함)을 스텝 3-1~3-3 값으로 업데이트
        for orig in orig_rows:
            item = dict(orig)
            item["_changes"] = {}
            enrich_names(item)

            v_cd = item["매입처"]
            c_cd = item["거래코드"]
            code = item["코드"]
            ym = item["ym"]
            yejeong = clean_num(item["예정금액"])

            # 후보 탐색: 동일 년월 + ((매입처 & 거래코드 일치) 또는 (코드 일치))
            candidates = [
                r for r in new_rows
                if r["_src_row"] not in used_src_rows
                and r["ym"] == ym
                and ((r["매입처"] == v_cd and r["거래코드"] == c_cd) or r["코드"] == code)
            ]
            #もし 거래코드가 약칭/타코드로 되어 있어 못 찾은 경우 동일 년월 + 동일 매입처 + 동일 예정금액으로 2차 탐색
            if not candidates:
                candidates = [
                    r for r in new_rows
                    if r["_src_row"] not in used_src_rows
                    and r["ym"] == ym
                    and r["매입처"] == v_cd
                    and abs(clean_num(r["예정금액"]) - yejeong) < 1.0
                ]

            match = None
            if candidates:
                candidates.sort(key=lambda r: abs(clean_num(r["예정금액"]) - yejeong))
                match = candidates[0]
                used_src_rows.add(match["_src_row"])
                matched_step3_rows.append(match)
            else:
                unmatched_orig_rows.append(item)

            if match:
                compare_fields = ["예정금액", "발행일자", "내용", "금액", "미결금액"]
                if sec_key == "sec3":
                    compare_fields.append("완결")

                changed = False
                for f in compare_fields:
                    old_val = item.get(f, "")
                    new_val = match.get(f, "")
                    if f in ("예정금액", "금액", "미결금액"):
                        if abs(clean_num(old_val) - clean_num(new_val)) >= 0.05:
                            item["_changes"][f] = {"old": clean_num(old_val), "new": clean_num(new_val)}
                            item[f] = new_val
                            changed = True
                        else:
                            # 미세 소수점 동기화
                            item[f] = new_val
                    else:
                        s_old = str(old_val or "").strip()
                        s_new = str(new_val or "").strip()
                        if s_new != s_old and (s_new or s_old):
                            item["_changes"][f] = {"old": s_old, "new": s_new}
                            item[f] = s_new
                            changed = True

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
                    mod_entry = {
                        "sec_key": sec_key,
                        "sec_title": SECTION_TITLES[sec_key],
                        "orig_row": item.get("_orig_row"),
                        "src_row": match.get("_src_row"),
                        "ym": ym,
                        "일자": item.get("일자", ""),
                        "매입처": item.get("매입처", ""),
                        "매입처명": item.get("매입처명", ""),
                        "거래코드": item.get("거래코드", ""),
                        "거래처": item.get("거래처", ""),
                        "거래처명": item.get("거래처명", ""),
                        "status": item["_status"],
                        "changes": item["_changes"],
                        "예정금액": clean_num(item.get("예정금액")),
                        "금액": clean_num(item.get("금액")),
                        "미결금액": clean_num(item.get("미결금액")),
                    }
                    modified_by_section[sec_key].append(mod_entry)
                    modified_all.append(mod_entry)
                else:
                    item["_status"] = "완결" if is_now_settled else "기존"
            else:
                is_now_settled = (
                    (sec_key == "sec3" and item.get("완결") == "완")
                    or (clean_num(item.get("예정금액")) != 0 and abs(clean_num(item.get("미결금액"))) < 1.0 and clean_num(item.get("금액")) != 0)
                )
                item["_status"] = "완결" if is_now_settled else "기존"

            merged.append(item)

        # ── 2) 기준월 해당건 (ym == base_month): 스텝2 원본에 스텝 3-1~3-3 기준월 값 추가
        added_base_month_rows: list[dict[str, Any]] = []
        for r in new_rows:
            if r["_src_row"] in used_src_rows:
                continue
            r_ym = r["ym"]
            yejeong = clean_num(r["예정금액"])
            migyeol = clean_num(r["미결금액"])
            geumaek = clean_num(r["금액"])

            if r_ym == base_month and (yejeong != 0 or migyeol != 0 or geumaek != 0):
                new_item = dict(r)
                enrich_names(new_item)
                is_settled = (
                    (sec_key == "sec3" and new_item.get("완결") == "완")
                    or (yejeong != 0 and abs(migyeol) < 1.0 and geumaek != 0)
                )
                new_item["_status"] = "완결" if is_settled else "신규"
                new_item["_changes"] = {}
                merged.append(new_item)
                added_base_month_rows.append(r)

        # ── 3) 최종검증 집계 (스텝 3-1~3-3 합계 vs 통합자료 합계 일치 검증)
        # (A) 기준월 해당건(ym == base_month) 합계 대조: 스텝 3 기준월 전체 vs 통합자료 기준월 전체
        step3_bm_rows = [
            r for r in new_rows
            if r["ym"] == base_month
            and (clean_num(r["예정금액"]) != 0 or clean_num(r["미결금액"]) != 0 or clean_num(r["금액"]) != 0)
        ]
        integ_bm_rows = [r for r in merged if r["ym"] == base_month]

        s3_bm_yj = sum(clean_num(r.get("예정금액")) for r in step3_bm_rows)
        s3_bm_gm = sum(clean_num(r.get("금액")) for r in step3_bm_rows)
        s3_bm_mg = sum(clean_num(r.get("미결금액")) for r in step3_bm_rows)

        in_bm_yj = sum(clean_num(r.get("예정금액")) for r in integ_bm_rows)
        in_bm_gm = sum(clean_num(r.get("금액")) for r in integ_bm_rows)
        in_bm_mg = sum(clean_num(r.get("미결금액")) for r in integ_bm_rows)

        # (B) 통합 반영 대상 전체(기준월 이전 업데이트분 + 기준월 추가분) 합계 대조:
        # 스텝 3에서 매칭·추가된 대상 행 합계(+ 원본 단독 행) vs 통합자료 각 항 합계
        step3_target_rows = matched_step3_rows + added_base_month_rows
        s3_tot_yj = sum(clean_num(r.get("예정금액")) for r in step3_target_rows) + sum(clean_num(r.get("예정금액")) for r in unmatched_orig_rows)
        s3_tot_gm = sum(clean_num(r.get("금액")) for r in step3_target_rows) + sum(clean_num(r.get("금액")) for r in unmatched_orig_rows)
        s3_tot_mg = sum(clean_num(r.get("미결금액")) for r in step3_target_rows) + sum(clean_num(r.get("미결금액")) for r in unmatched_orig_rows)
        s3_tot_cnt = len(step3_target_rows) + len(unmatched_orig_rows)

        in_tot_yj = sum(clean_num(r.get("예정금액")) for r in merged)
        in_tot_gm = sum(clean_num(r.get("금액")) for r in merged)
        in_tot_mg = sum(clean_num(r.get("미결금액")) for r in merged)
        in_tot_cnt = len(merged)

        # (C) 스텝 3 파일 전체 누적 합계 (참고용)
        s3_raw_yj = sum(clean_num(r.get("예정금액")) for r in new_rows)
        s3_raw_gm = sum(clean_num(r.get("금액")) for r in new_rows)
        s3_raw_mg = sum(clean_num(r.get("미결금액")) for r in new_rows)

        diff_tot_yj = in_tot_yj - s3_tot_yj
        diff_tot_gm = in_tot_gm - s3_tot_gm
        diff_tot_mg = in_tot_mg - s3_tot_mg

        diff_bm_yj = in_bm_yj - s3_bm_yj
        diff_bm_gm = in_bm_gm - s3_bm_gm
        diff_bm_mg = in_bm_mg - s3_bm_mg

        is_valid = (
            abs(diff_tot_yj) < 1.0
            and abs(diff_tot_gm) < 1.0
            and abs(diff_tot_mg) < 1.0
            and abs(diff_bm_mg) < 1.0
        )

        verification_report.append({
            "sec_key": sec_key,
            "step_label": step_label,
            "sec_title": SECTION_TITLES[sec_key],
            "prior_orig_count": sum(1 for r in orig_rows if r["ym"] != base_month),
            "prior_matched_count": sum(1 for r in matched_step3_rows if r["ym"] != base_month),
            "prior_modified_count": len(modified_by_section[sec_key]),
            "base_month_added_count": len(added_base_month_rows),
            "base_month_total_count": len(integ_bm_rows),
            "step3_target": {
                "count": s3_tot_cnt,
                "예정금액": s3_tot_yj,
                "집행금액": s3_tot_gm,
                "미결금액": s3_tot_mg,
            },
            "integrated": {
                "count": in_tot_cnt,
                "예정금액": in_tot_yj,
                "집행금액": in_tot_gm,
                "미결금액": in_tot_mg,
            },
            "diff_total": {
                "count": in_tot_cnt - s3_tot_cnt,
                "예정금액": diff_tot_yj,
                "집행금액": diff_tot_gm,
                "미결금액": diff_tot_mg,
            },
            "step3_base_month": {
                "count": len(step3_bm_rows),
                "예정금액": s3_bm_yj,
                "집행금액": s3_bm_gm,
                "미결금액": s3_bm_mg,
            },
            "integrated_base_month": {
                "count": len(integ_bm_rows),
                "예정금액": in_bm_yj,
                "집행금액": in_bm_gm,
                "미결금액": in_bm_mg,
            },
            "diff_base_month": {
                "count": len(integ_bm_rows) - len(step3_bm_rows),
                "예정금액": diff_bm_yj,
                "집행금액": diff_bm_gm,
                "미결금액": diff_bm_mg,
            },
            "step3_raw_file": {
                "count": len(new_rows),
                "예정금액": s3_raw_yj,
                "집행금액": s3_raw_gm,
                "미결금액": s3_raw_mg,
            },
            "is_valid": is_valid,
        })

        return merged

    sec1_merged = merge_section("sec1", "Step 3-1 (사후미결)", orig_data["sections"]["sec1"], sahu_data["records"])
    sec2_merged = [enrich_names(dict(r, _status="기존", _changes={})) for r in orig_data["sections"]["sec2"]]
    sec3_merged = merge_section("sec3", "Step 3-2 (저가미결)", orig_data["sections"]["sec3"], jeoga_data["records"])
    sec4_merged = merge_section("sec4", "Step 3-3 (약가미결)", orig_data["sections"]["sec4"], yakga_data["records"])

    sections_merged = {
        "sec1": sec1_merged,
        "sec2": sec2_merged,
        "sec3": sec3_merged,
        "sec4": sec4_merged,
    }

    # 매입처별 요약 리포트 집계
    vendor_agg: dict[str, dict[str, Any]] = {}
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
            "label": SECTION_TITLES[sec_key],
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
        "kpis": {
            "총_예정금액": total_yejeong,
            "총_집행금액": total_geumaek,
            "총_미결금액": total_migyeol,
            "총_건수": sum(len(v) for v in sections_merged.values()),
            "매입처_수": len(vendor_summary),
            "상태별_건수": status_counts,
            "수정_리포트_건수": len(modified_all),
            "검증_모두_일치": all(v["is_valid"] for v in verification_report),
        },
        "verification_report": verification_report,
        "modified_by_section": modified_by_section,
        "modified_all": modified_all,
        "section_summary": section_summary,
        "vendor_summary": vendor_summary,
        "sections": sections_merged,
    }


# ──────────────────────────────────────────────────────────────
# 5. 엑셀 생성 엔진 (타이틀 초기화 및 사후미결 / 사후미결(바슈) / 저가미결 / 약가미결 명칭 부여)
# ──────────────────────────────────────────────────────────────
def generate_integrated_excel(analysis_result: dict[str, Any], output_path: str | Path) -> str:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "미결(병원부)"
    ws.views.sheetView[0].showGridLines = True

    f_title = Font(name="맑은 고딕", size=11, bold=True, color="FFFFFF")
    f_th = Font(name="맑은 고딕", size=9, bold=True, color="1E293B")
    f_td = Font(name="맑은 고딕", size=9, color="0F172A")
    f_td_num = Font(name="맑은 고딕", size=9, color="0F172A")
    f_td_neg = Font(name="맑은 고딕", size=9, bold=True, color="DC2626")
    f_td_settled = Font(name="맑은 고딕", size=9, bold=True, color="059669")
    f_td_mod = Font(name="맑은 고딕", size=9, bold=True, color="B45309")

    fill_top_bar = PatternFill("solid", fgColor="1E3A8A")
    fill_th = PatternFill("solid", fgColor="F1F5F9")
    fill_zebra = PatternFill("solid", fgColor="F8FAFC")
    fill_white = PatternFill("solid", fgColor="FFFFFF")
    fill_new = PatternFill("solid", fgColor="EFF6FF")
    fill_mod = PatternFill("solid", fgColor="FFFBEB")
    fill_settled = PatternFill("solid", fgColor="ECFDF5")

    thin_border_side = Side(style="thin", color="CBD5E1")
    med_navy_side = Side(style="medium", color="1E3A8A")
    double_bottom_side = Side(style="double", color="475569")

    b_data = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    b_th = Border(left=thin_border_side, right=thin_border_side, top=med_navy_side, bottom=double_bottom_side)

    align_center = Alignment(horizontal="center", vertical="center", wrap_text=False)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=False)
    align_right = Alignment(horizontal="right", vertical="center", wrap_text=False)

    num_fmt_krw = "#,##0;[Red]-#,##0;\"-\""

    sections = analysis_result["sections"]
    base_month = analysis_result.get("base_month", "")

    # ── Row 1: 상단 요약 컨트롤 바
    ws.row_dimensions[1].height = 26
    for c in range(1, 26):
        cell = ws.cell(1, c, "")
        cell.fill = fill_top_bar
        cell.font = f_title
        cell.alignment = align_center

    ws.cell(1, 2, f"Q필터 : 기준월 [{base_month}]")
    ws.cell(1, 5, "정")
    ws.cell(1, 7, "책")
    ws.cell(1, 9, "범례: 확정 / 예외추가% / 신규(청색) / 수정(황색) / 완결(녹색)")
    ws.cell(1, 12, "집   행        미결금액:")
    ws.cell(1, 17, "※ 수금할인&할인조정 미결누적 관리 (통합 리포트)")
    ws.cell(1, 17).alignment = align_left

    curr_row = 2

    def write_section_banner(row_idx: int, title: str, max_cols: int):
        ws.row_dimensions[row_idx].height = 22
        # 항목 타이틀 행: 초기화 후 문자는 좌측 첫열(A열)에 배치하고 채우기, 테두리 삭제
        for c in range(1, max_cols + 1):
            cell = ws.cell(row_idx, c, None)
            cell.fill = PatternFill(fill_type=None)
            cell.border = Border()
        title_cell = ws.cell(row_idx, 1, title)
        title_cell.font = Font(name="맑은 고딕", size=10, bold=True, color="0F172A")
        title_cell.alignment = align_left

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

                if col_name in ("예정금액", "금액", "미결금액", "참조", "참조-현 내역", "예정 차", "미결 차", "오차분"):
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
                elif col_name in ("매입월", "매입처", "사전%", "매입%", "수금%", "년%", "일자", "발행일자", "거래코드", "잡행일", "완결"):
                    cell.value = str(val or "")
                    cell.font = f_td_settled if (col_name == "완결" and val == "완") else f_td
                    cell.alignment = align_center
                else:
                    cell.value = str(val or "")
                    cell.font = f_td
                    cell.alignment = align_left

            r_cursor += 1
        return r_cursor

    # ── 항목 1: 사후미결
    write_section_banner(curr_row, SECTION_TITLES["sec1"], len(SEC1_COLS))
    curr_row += 1
    write_header_row(curr_row, SEC1_COLS)
    curr_row += 1
    curr_row = write_data_rows(curr_row, sections["sec1"], SEC1_COLS)

    curr_row += 1

    # ── 항목 2: 사후미결(바슈)
    write_section_banner(curr_row, SECTION_TITLES["sec2"], len(SEC2_COLS))
    curr_row += 1
    write_header_row(curr_row, SEC2_COLS)
    curr_row += 1
    curr_row = write_data_rows(curr_row, sections["sec2"], SEC2_COLS)

    curr_row += 1

    # ── 항목 3: 저가미결
    write_section_banner(curr_row, SECTION_TITLES["sec3"], len(SEC3_COLS))
    curr_row += 1
    write_header_row(curr_row, SEC3_COLS)
    curr_row += 1
    curr_row = write_data_rows(curr_row, sections["sec3"], SEC3_COLS)

    curr_row += 1

    # ── 항목 4: 약가미결
    write_section_banner(curr_row, SECTION_TITLES["sec4"], len(SEC4_COLS))
    curr_row += 1
    write_header_row(curr_row, SEC4_COLS)
    curr_row += 1
    curr_row = write_data_rows(curr_row, sections["sec4"], SEC4_COLS)

    # 상단 O1(15열)에 전체 미결금액 SUBTOTAL 수식 입력
    last_row = max(curr_row - 1, 4)
    p1 = ws.cell(1, 15, f"=SUBTOTAL(9,O4:O{last_row})")
    p1.font = Font(name="맑은 고딕", size=11, bold=True, color="FDE047")
    p1.fill = fill_top_bar
    p1.number_format = num_fmt_krw
    p1.alignment = align_right

    # 한 화면에 볼 수 있도록 열너비 적정 축소 조정 (1~25열)
    col_widths = {
        1: 9,   # 매입월
        2: 7,   # 매입처
        3: 15,  # 매입처명
        4: 6,   # 조건
        5: 5,   # 사전%
        6: 5,   # 매입%
        7: 5,   # 수금%
        8: 5,   # 년%
        9: 8,   # 일자
        10: 16, # 적요
        11: 12, # 예정금액
        12: 10, # 발행일자
        13: 10, # 내용
        14: 12, # 금액
        15: 12, # 미결금액
        16: 10, # 거래처
        17: 14, # 비고
        18: 8,  # 거래코드
        19: 18, # 거래처명
        20: 11, # 참조
        21: 11, # 참조-현 내역
        22: 11, # 예정 차
        23: 10, # 미결 차
        24: 10, # 잡행일
        25: 6,  # 완결
    }
    for c_idx, w in col_widths.items():
        ws.column_dimensions[get_column_letter(c_idx)].width = w

    ws.freeze_panes = "A4"

    # ══════════════════════════════════════════════════════════
    # Sheet 2: 매입처별 요약 리포트 (각 필드 합계 포함)
    # ══════════════════════════════════════════════════════════
    ws_sum = wb.create_sheet(title="매입처별 요약 리포트")
    ws_sum.views.sheetView[0].showGridLines = True

    ws_sum.row_dimensions[1].height = 28
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

    v_list = analysis_result["vendor_summary"]
    for i, v in enumerate(v_list, start=3):
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

    # 매입처별 요약 리포트 하단 합계 행
    tot_row_idx = len(v_list) + 3
    ws_sum.row_dimensions[tot_row_idx].height = 22
    totals = [
        "합계", f"총 {len(v_list)}개 매입처",
        sum(v["사후_예정"] for v in v_list),
        sum(v["사후_집행"] for v in v_list),
        sum(v["사후_미결"] for v in v_list),
        sum(v["저가_예정"] for v in v_list),
        sum(v["저가_집행"] for v in v_list),
        sum(v["저가_미결"] for v in v_list),
        sum(v["약가_예정"] for v in v_list),
        sum(v["약가_집행"] for v in v_list),
        sum(v["약가_미결"] for v in v_list),
        sum(v["총_예정금액"] for v in v_list),
        sum(v["총_집행금액"] for v in v_list),
        sum(v["총_미결금액"] for v in v_list),
        f"신규 {sum(v['신규_건수'] for v in v_list)} / 수정 {sum(v['수정_건수'] for v in v_list)} / 완결 {sum(v['완결_건수'] for v in v_list)}",
    ]
    for c_idx, val in enumerate(totals, start=1):
        c = ws_sum.cell(tot_row_idx, c_idx, val)
        c.fill = fill_th
        c.border = b_th
        if 3 <= c_idx <= 14:
            c.number_format = num_fmt_krw
            c.alignment = align_right
            c.font = f_td_neg if clean_num(val) < 0 else f_th
        else:
            c.alignment = align_center
            c.font = f_th

    sum_widths = [11, 20, 13, 13, 13, 13, 13, 13, 13, 13, 13, 14, 14, 14, 20]
    for c_idx, w in enumerate(sum_widths, start=1):
        ws_sum.column_dimensions[get_column_letter(c_idx)].width = w
    ws_sum.freeze_panes = "C3"

    # ══════════════════════════════════════════════════════════
    # Sheet 3: 최종검증 및 수정사항 리포트
    # ══════════════════════════════════════════════════════════
    ws_ver = wb.create_sheet(title="최종검증 및 수정리포트")
    ws_ver.views.sheetView[0].showGridLines = True

    ws_ver.row_dimensions[1].height = 28
    for c in range(1, 13):
        cell = ws_ver.cell(1, c, "")
        cell.fill = fill_top_bar
        cell.font = f_title
    ws_ver.cell(1, 1, f"✅ 최종검증(Step 3 합계 vs 통합자료 합계) 및 기준월 이전건 수정 리포트 (기준월: {base_month})").alignment = align_left

    ver_headers = [
        "항목명", "대조 대상(Step)",
        "Step 3 반영건수", "통합자료 건수",
        "Step 3 예정금액 합계", "통합자료 예정금액 합계",
        "Step 3 집행금액 합계", "통합자료 집행금액 합계",
        "Step 3 미결금액 합계", "통합자료 미결금액 합계",
        "미결 차액(검증)", "일치 여부"
    ]
    ws_ver.row_dimensions[2].height = 24
    for c_idx, h_text in enumerate(ver_headers, start=1):
        c = ws_ver.cell(2, c_idx, h_text)
        c.font = f_th
        c.fill = fill_th
        c.border = b_th
        c.alignment = align_center

    v_row = 3
    for vr in analysis_result.get("verification_report", []):
        ws_ver.row_dimensions[v_row].height = 20
        vals = [
            vr["sec_title"],
            vr["step_label"],
            vr["step3_target"]["count"],
            vr["integrated"]["count"],
            vr["step3_target"]["예정금액"],
            vr["integrated"]["예정금액"],
            vr["step3_target"]["집행금액"],
            vr["integrated"]["집행금액"],
            vr["step3_target"]["미결금액"],
            vr["integrated"]["미결금액"],
            vr["diff_total"]["미결금액"],
            "일치 (검증완료)" if vr["is_valid"] else "불일치 확인필요",
        ]
        for c_idx, val in enumerate(vals, start=1):
            c = ws_ver.cell(v_row, c_idx, val)
            c.fill = fill_settled if vr["is_valid"] else fill_mod
            c.border = b_data
            if 5 <= c_idx <= 11:
                c.number_format = num_fmt_krw
                c.alignment = align_right
                c.font = f_td_neg if clean_num(val) < 0 else f_td_num
            elif c_idx in (3, 4, 12):
                c.alignment = align_center
                c.font = f_td_settled if (c_idx == 12 and vr["is_valid"]) else f_td
            else:
                c.alignment = align_left
                c.font = f_th if c_idx == 1 else f_td
        v_row += 1

    # 기준월 이전건 항목별 수정사항 테이블
    v_row += 2
    ws_ver.cell(v_row, 1, "📝 기준월 이전건 업데이트(수정) 상세 리포트").font = Font(name="맑은 고딕", size=10, bold=True, color="0F172A")
    v_row += 1

    mod_headers = ["항목", "년월", "매입처코드", "매입처명", "거래처명", "상태", "수정 필드 및 변경 내역 (변경 전 → 변경 후)"]
    ws_ver.row_dimensions[v_row].height = 22
    for c_idx, h_text in enumerate(mod_headers, start=1):
        c = ws_ver.cell(v_row, c_idx, h_text)
        c.font = f_th
        c.fill = fill_th
        c.border = b_th
        c.alignment = align_center
    v_row += 1

    for m in analysis_result.get("modified_all", []):
        ws_ver.row_dimensions[v_row].height = 20
        ch_parts = []
        for f_name, ch_val in m.get("changes", {}).items():
            old_v = ch_val.get("old", "")
            new_v = ch_val.get("new", "")
            if isinstance(old_v, (int, float)) or isinstance(new_v, (int, float)):
                ch_parts.append(f"{f_name}: {clean_num(old_v):,.0f} → {clean_num(new_v):,.0f}")
            else:
                ch_parts.append(f"{f_name}: '{old_v or '공란'}' → '{new_v or '공란'}'")
        vals = [
            m["sec_title"],
            m["ym"],
            m["매입처"],
            m["매입처명"],
            m["거래처명"] or m["거래처"],
            m["status"],
            " / ".join(ch_parts),
        ]
        for c_idx, val in enumerate(vals, start=1):
            c = ws_ver.cell(v_row, c_idx, val)
            c.fill = fill_mod
            c.border = b_data
            c.font = f_td
            c.alignment = align_center if c_idx in (1, 2, 3, 6) else align_left
        v_row += 1

    ver_widths = [14, 18, 13, 13, 16, 16, 16, 16, 16, 16, 14, 16]
    for c_idx, w in enumerate(ver_widths, start=1):
        ws_ver.column_dimensions[get_column_letter(c_idx)].width = w

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out_p))
    return str(out_p)
