#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
지오영 병원부 지급품의서(.xls/.xlsx) -> 결재집행비교(.xlsx) 자동 반영 및 금액 검증 엔진.
- Python이 XLS/XLSX를 분석하고 매칭/합산/분리/행삽입 계획을 생성
- 실제 XLSX 수정 및 저장은 PowerShell Excel COM(apply_excel_com.ps1)으로 수행하여 엑셀 서식 100% 유지
"""

import argparse
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
import json
import os
import re
import subprocess
import sys
import tempfile

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
import xlrd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def norm_code(val):
    if val is None:
        return ""
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return str(val).strip()
    if isinstance(val, int):
        return str(val)
    s = str(val).strip()
    if s.endswith(".0") and s[:-2].isdigit():
        return s[:-2]
    return s


def norm_name(val):
    if val is None:
        return ""
    s = str(val).strip().lower()
    s = re.sub(r"\s+", "", s)
    return s


def strip_company_prefix(val):
    s = norm_name(val)
    for tok in ("(주)", "㈜", "주식회사", "(유)", "유한회사"):
        s = s.replace(tok, "")
    return s


def extract_paren_tokens(val):
    if not val:
        return []
    found = re.findall(r"\(([^)]+)\)", str(val))
    tokens = []
    for f in found:
        for part in re.split(r"[/,.\s:+]+", f.strip().lower()):
            if len(part) >= 2 and not re.match(r"^\d{2}(\.\d+)?(re)?$", part):
                tokens.append(part)
    return tokens


def text_similarity(a, b):
    na = norm_name(a)
    nb = norm_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if na in nb or nb in na:
        return 0.85
    return SequenceMatcher(None, na, nb).ratio()


def to_number(val):
    if val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_excel_date(val, datemode=0):
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, (int, float)) and val > 30000:
        try:
            dt = xlrd.xldate_as_datetime(val, datemode)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None
    s = str(val).strip()
    m = re.search(r"(20\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


def parse_proposal_xls(xls_path):
    """지오영병원부 지급품의서(.xls 또는 .xlsx) 파싱"""
    ext = os.path.splitext(xls_path)[1].lower()
    rows_raw = []
    datemode = 0

    if ext == ".xls":
        wb = xlrd.open_workbook(xls_path)
        datemode = wb.datemode
        sh = wb.sheet_by_index(0)
        sheet_name = sh.name
        for r in range(sh.nrows):
            rows_raw.append([sh.cell_value(r, c) for c in range(sh.ncols)])
    else:
        wb = openpyxl.load_workbook(xls_path, data_only=True)
        ws = wb.worksheets[0]
        sheet_name = ws.title
        for r in range(1, ws.max_row + 1):
            rows_raw.append([ws.cell(r, c).value for c in range(1, ws.max_column + 1)])

    # 헤더 행 탐지 (제조사명, 매출처 포함)
    header_idx = 3
    for idx, rvals in enumerate(rows_raw[:15]):
        joined = " ".join(str(x or "") for x in rvals)
        if "제조사명" in joined and "매출처" in joined:
            header_idx = idx
            break

    # 기본 열 인덱스 (0-based): C=2 매입코드, D=3 납품코드, E=4 제조사명, F=5 매출처, G=6 현금, H=7 기업구매자금, I=8 만기일
    col_buy, col_del, col_maker, col_cust, col_cash, col_bill, col_due = 2, 3, 4, 5, 6, 7, 8
    for c, v in enumerate(rows_raw[header_idx]):
        sv = re.sub(r"\s+", "", str(v or ""))
        if "매입" in sv:
            col_buy = c
        elif "납품" in sv:
            col_del = c
        elif "제조사" in sv:
            col_maker = c
        elif "매출처" in sv:
            col_cust = c

    mode = "현금"
    items = []
    declared_cash_subtotal = None
    declared_bill_subtotal = None
    declared_total = None

    start_row = header_idx + 2  # R4 헤더, R5 서브헤더, R6 데이터 시작
    for idx in range(start_row, len(rows_raw)):
        rvals = rows_raw[idx]
        if len(rvals) <= col_bill:
            continue

        bc = norm_code(rvals[col_buy])
        dc = norm_code(rvals[col_del])
        maker = str(rvals[col_maker] or "").strip()
        cust = str(rvals[col_cust] or "").strip()
        maker_ns = re.sub(r"\s+", "", maker)
        cash_val = to_number(rvals[col_cash])
        bill_val = to_number(rvals[col_bill])
        due_val = rvals[col_due] if len(rvals) > col_due else None

        # 섹션 전환 및 소계/합계 행 판별 (매입코드가 비어있을 때만 특수행으로 판정!)
        if not bc:
            if maker_ns == "소계":
                if mode == "현금" and cash_val > 0:
                    declared_cash_subtotal = cash_val
                continue
            if maker_ns == "어음":
                # 헤더 행인지 하단 요약 행인지 구분
                if str(rvals[col_cash] or "").strip() == "현금" or "기업구매자금" in str(rvals[col_bill] or ""):
                    mode = "어음"
                    continue
                if bill_val > 0:
                    declared_bill_subtotal = bill_val
                    continue
            if "현금/구매자금" in maker_ns or "현금/어음" in maker_ns:
                if bill_val > 0 and declared_cash_subtotal is None:
                    declared_cash_subtotal = bill_val
                continue
            if maker_ns == "합계":
                if bill_val > 0:
                    declared_total = bill_val
                elif cash_val > 0:
                    declared_total = cash_val
                break
            if not maker and not cust:
                continue

        # 실제 데이터 행
        if mode == "현금":
            if cash_val != 0:
                items.append({
                    "sourceRow": idx + 1,
                    "kind": "현금",
                    "buyerCode": bc,
                    "buyerName": maker,
                    "customerCode": dc,
                    "customerName": cust,
                    "amount": round(cash_val),
                    "dueDate": None,
                })
            if bill_val != 0:
                items.append({
                    "sourceRow": idx + 1,
                    "kind": "어음",
                    "buyerCode": bc,
                    "buyerName": maker,
                    "customerCode": dc,
                    "customerName": cust,
                    "amount": round(bill_val),
                    "dueDate": parse_excel_date(due_val, datemode),
                })
        else:
            if bill_val != 0:
                items.append({
                    "sourceRow": idx + 1,
                    "kind": "어음",
                    "buyerCode": bc,
                    "buyerName": maker,
                    "customerCode": dc,
                    "customerName": cust,
                    "amount": round(bill_val),
                    "dueDate": parse_excel_date(due_val, datemode),
                })
            if cash_val != 0:
                items.append({
                    "sourceRow": idx + 1,
                    "kind": "현금",
                    "buyerCode": bc,
                    "buyerName": maker,
                    "customerCode": dc,
                    "customerName": cust,
                    "amount": round(cash_val),
                    "dueDate": None,
                })

    cash_sum = sum(x["amount"] for x in items if x["kind"] == "현금")
    bill_sum = sum(x["amount"] for x in items if x["kind"] == "어음")
    total_sum = cash_sum + bill_sum

    return {
        "sheetName": sheet_name,
        "items": items,
        "cashCount": sum(1 for x in items if x["kind"] == "현금"),
        "billCount": sum(1 for x in items if x["kind"] == "어음"),
        "cashSum": cash_sum,
        "billSum": bill_sum,
        "totalSum": total_sum,
        "declaredCashSubtotal": round(declared_cash_subtotal) if declared_cash_subtotal is not None else None,
        "declaredBillSubtotal": round(declared_bill_subtotal) if declared_bill_subtotal is not None else None,
        "declaredTotal": round(declared_total) if declared_total is not None else None,
    }


def analyze_comparison_xlsx(xlsx_path):
    """결재집행비교(.xlsx) 내역 및 집계 시트 구조 분석"""
    wb = openpyxl.load_workbook(xlsx_path, data_only=False)

    # 내역 시트 찾기
    detail_sheet_name = None
    for name in wb.sheetnames:
        if "내역" in name:
            detail_sheet_name = name
            break
    if not detail_sheet_name:
        raise ValueError(f"'내역' 시트를 찾을 수 없습니다. (시트 목록: {wb.sheetnames})")

    ws = wb[detail_sheet_name]

    # 헤더 행(보통 3행)에서 당월 예정금액 열(G=7), 만기일 열(I=9) 탐색
    amount_col = 7
    due_date_col = 9
    for c in range(1, min(20, ws.max_column + 1)):
        hv = re.sub(r"\s+", "", str(ws.cell(3, c).value or ""))
        if "예정" in hv and "금액" in hv:
            amount_col = c
        elif "예정" in hv and "만기일" in hv:
            due_date_col = c

    bill_start = 4
    bill_subtotal_row = None
    cash_start = None
    cash_subtotal_row = None
    total_row = None
    rows_info = []

    for r in range(4, ws.max_row + 1):
        b_val = ws.cell(r, 2).value
        c_val = ws.cell(r, 3).value
        d_val = ws.cell(r, 4).value
        e_val = ws.cell(r, 5).value
        f_val = ws.cell(r, 6).value
        h_val = ws.cell(r, 8).value

        e_ns = re.sub(r"\s+", "", str(e_val or ""))
        if b_val is None and c_val is None:
            if "어음소계" in e_ns:
                bill_subtotal_row = r
                cash_start = r + 1
                continue
            if "현금소계" in e_ns:
                cash_subtotal_row = r
                continue
            if e_ns == "합계":
                total_row = r
                continue

        h_str = str(h_val or "").strip()
        if h_str in ("어음", "현금"):
            rows_info.append({
                "row": r,
                "kind": h_str,
                "buyerCode": norm_code(b_val),
                "buyerName": str(c_val or "").strip(),
                "customerCode": norm_code(d_val),
                "customerName": str(e_val or "").strip(),
                "prevAmount": to_number(f_val),
            })

    if not bill_subtotal_row or not cash_subtotal_row or not total_row:
        raise ValueError(
            f"내역 시트에서 소계/합계 행을 찾지 못했습니다. "
            f"(어음소계={bill_subtotal_row}, 현금소계={cash_subtotal_row}, 합계={total_row})"
        )

    # 집계 시트 분석
    summary_sheet_name = None
    summary_bill_row = 0
    summary_cash_row = 0
    summary_total_row = 0
    summary_amount_col = 4
    if "집계" in wb.sheetnames:
        summary_sheet_name = "집계"
        ws_sum = wb["집계"]
        for c in range(1, min(12, ws_sum.max_column + 1)):
            hv = re.sub(r"\s+", "", str(ws_sum.cell(5, c).value or ""))
            if "예정" in hv and "금액" in hv:
                summary_amount_col = c
                break
        for r in range(5, min(15, ws_sum.max_row + 1)):
            a_ns = re.sub(r"\s+", "", str(ws_sum.cell(r, 1).value or ""))
            if "어음소계" in a_ns:
                summary_bill_row = r
            elif "현금소계" in a_ns:
                summary_cash_row = r
            elif a_ns == "합계":
                summary_total_row = r

    return {
        "detailSheet": detail_sheet_name,
        "amountCol": amount_col,
        "dueDateCol": due_date_col,
        "billStartRow": bill_start,
        "billSubtotalRow": bill_subtotal_row,
        "cashStartRow": cash_start,
        "cashSubtotalRow": cash_subtotal_row,
        "totalRow": total_row,
        "rows": rows_info,
        "summarySheet": summary_sheet_name,
        "summaryBillRow": summary_bill_row,
        "summaryCashRow": summary_cash_row,
        "summaryTotalRow": summary_total_row,
        "summaryAmountCol": summary_amount_col,
    }


def match_and_build_plan(proposal, comp):
    """지급품의서 항목을 결재집행비교 내역 시트 행에 정밀 매칭(합산/분리/누락행 삽입)"""
    # 인덱스 구축
    by_code_key = defaultdict(list)  # (kind, buyerCode, customerCode) -> [row_info]
    by_name_key = defaultdict(list)  # (kind, normBuyer, customerCode) -> [row_info]
    for row_info in comp["rows"]:
        by_code_key[(row_info["kind"], row_info["buyerCode"], row_info["customerCode"])].append(row_info)
        by_name_key[(row_info["kind"], strip_company_prefix(row_info["buyerName"]), row_info["customerCode"])].append(row_info)

    # XLS 항목을 (kind, buyerCode, customerCode) 그룹으로 묶기
    xls_groups = defaultdict(list)
    for item in proposal["items"]:
        xls_groups[(item["kind"], item["buyerCode"], item["customerCode"])].append(item)

    row_amounts = defaultdict(int)
    row_due_dates = {}
    insert_bill = []
    insert_cash = []
    merged_logs = []
    split_logs = []

    def assign_row(row_num, item, reason):
        row_amounts[row_num] += item["amount"]
        if item["dueDate"] and row_num not in row_due_dates:
            row_due_dates[row_num] = item["dueDate"]
        return reason

    for (kind, bc, dc), group_items in xls_groups.items():
        candidates = list(by_code_key.get((kind, bc, dc), []))

        # 코드 매칭 실패 시 매입처명 + 거래처코드 보조 매칭
        if not candidates and group_items:
            nb = strip_company_prefix(group_items[0]["buyerName"])
            candidates = list(by_name_key.get((kind, nb, dc), []))

        # 후보가 전혀 없는 경우 -> 누락 행 삽입
        if not candidates:
            for item in group_items:
                if kind == "어음":
                    insert_bill.append(item)
                else:
                    insert_cash.append(item)
            continue

        # 후보가 정확히 1개인 경우 -> 단일 또는 합산 배정
        if len(candidates) == 1:
            target = candidates[0]
            for item in group_items:
                assign_row(target["row"], item, "exact_or_sum")
            if len(group_items) > 1:
                merged_logs.append({
                    "kind": kind,
                    "row": target["row"],
                    "buyerCode": bc,
                    "buyerName": target["buyerName"],
                    "customerCode": dc,
                    "customerName": target["customerName"],
                    "count": len(group_items),
                    "totalAmount": sum(x["amount"] for x in group_items),
                })
            continue

        # 후보가 여러 개인 경우 (M >= 2)
        # 각 XLS 항목에 대해 최적 후보 매칭 (분리 우선, 동일 키 중복 행 1:1 배정 지원)
        used_rows = set()

        # 품목별 분리 관리 패턴 여부 확인 (예: D9333 의약품유통(품목명))
        cand_paren_sets = [set(extract_paren_tokens(c["customerName"])) for c in candidates]
        is_itemized_split = (
            dc.upper() == "D9333"
            or (len(candidates) >= 3 and sum(1 for s in cand_paren_sets if s) >= 2 and len({frozenset(s) for s in cand_paren_sets if s}) >= 2)
        )

        for item in group_items:
            item_buyer_s = strip_company_prefix(item["buyerName"])
            item_cust_tokens = set(extract_paren_tokens(item["customerName"]))

            scored = []
            for c in candidates:
                c_buyer_s = strip_company_prefix(c["buyerName"])
                buyer_sim = 1.0 if item_buyer_s == c_buyer_s else text_similarity(item_buyer_s, c_buyer_s)
                cust_sim = text_similarity(item["customerName"], c["customerName"])

                c_tokens = set(extract_paren_tokens(c["customerName"]))
                token_overlap = len(item_cust_tokens & c_tokens) if (item_cust_tokens and c_tokens) else 0

                # 점수 산정: 매입처명 일치 > 괄호 품목명 일치 > 거래처명 유사도 > 미사용 행 우선 > 전월 금액 활성 행 우선
                unused_bonus = 0.25 if c["row"] not in used_rows else 0.0
                active_bonus = 0.1 if c["prevAmount"] > 0 else 0.0
                score = (
                    buyer_sim * 3.0
                    + (2.5 if token_overlap > 0 else 0.0)
                    + cust_sim * 1.5
                    + unused_bonus
                    + active_bonus
                )
                scored.append((score, token_overlap, buyer_sim, cust_sim, c))

            scored.sort(key=lambda x: x[0], reverse=True)
            best_score, best_overlap, best_bsim, best_csim, best_cand = scored[0]

            # 품목별 분리 관리(D9333 등)에서 괄호 품목명이 명시되어 있는데 어떤 기존 행과도 품목명이 안 겹치면 새 행 삽입
            if is_itemized_split and item_cust_tokens and best_overlap == 0 and best_csim < 0.85:
                if kind == "어음":
                    insert_bill.append(item)
                else:
                    insert_cash.append(item)
                continue

            # 이미 사용된 행에 또 배정해야 하는 경우:
            # 같은 매입처명+거래처명 미사용 행이 있으면 거기에 분리, 아니면 기존 행에 합산
            assign_row(best_cand["row"], item, "multi_match")
            used_rows.add(best_cand["row"])

        if len(group_items) > 1:
            if len(used_rows) > 1:
                split_logs.append({
                    "kind": kind,
                    "buyerCode": bc,
                    "buyerName": group_items[0]["buyerName"],
                    "customerCode": dc,
                    "sourceCount": len(group_items),
                    "matchedRows": sorted(list(used_rows)),
                    "totalAmount": sum(x["amount"] for x in group_items),
                })
            elif len(used_rows) == 1:
                only_row = next(iter(used_rows))
                merged_logs.append({
                    "kind": kind,
                    "row": only_row,
                    "buyerCode": bc,
                    "buyerName": group_items[0]["buyerName"],
                    "customerCode": dc,
                    "customerName": group_items[0]["customerName"],
                    "count": len(group_items),
                    "totalAmount": sum(x["amount"] for x in group_items),
                })

    updates = [
        {
            "row": r,
            "amount": amt,
            "dueDate": row_due_dates.get(r),
        }
        for r, amt in sorted(row_amounts.items())
    ]

    return {
        "updates": updates,
        "insertBill": insert_bill,
        "insertCash": insert_cash,
        "mergedLogs": merged_logs,
        "splitLogs": split_logs,
    }


def run_excel_com(plan_data):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ps1_path = os.path.join(script_dir, "apply_excel_com.ps1")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as tf:
        json.dump(plan_data, tf, ensure_ascii=False)
        plan_path = tf.name

    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1_path, "-PlanPath", plan_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        if proc.returncode != 0:
            raise RuntimeError(f"Excel COM 실행 실패 (code={proc.returncode}): {stdout or stderr}")

        # 마지막 JSON 라인 파싱
        lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
        if not lines:
            raise RuntimeError(f"Excel COM 출력이 비어있습니다. stderr={stderr}")
        return json.loads(lines[-1])
    finally:
        try:
            os.remove(plan_path)
        except OSError:
            pass


def generate_vendor_summary_xlsx(proposal, out_path):
    """
    지급품의서 예정금액 기준으로
    '월별자금수지계획표(병원부)YYYY.MM_첨부(매입처별 집계표)_예정.xlsx' 생성.
    기존 양식(Sheet2, 숨김 A열 코드, B~G열, 파란 헤더 #0070C0, 회색 요약행 #D9D9D9, SUBTOTAL 수식)과 동일하게 유지.
    """
    grouped = {}
    for item in proposal["items"]:
        key = (item["kind"], item["buyerCode"], item["buyerName"])
        if key not in grouped:
            grouped[key] = {
                "kind": item["kind"],
                "buyerCode": item["buyerCode"],
                "buyerName": item["buyerName"],
                "amount": 0,
                "dueDate": item["dueDate"],
            }
        grouped[key]["amount"] += item["amount"]
        # 어음 만기일이 여러 개인 경우 가장 늦은 만기일(또는 최초 유효 만기일) 유지
        if item["dueDate"]:
            if not grouped[key]["dueDate"] or item["dueDate"] > grouped[key]["dueDate"]:
                grouped[key]["dueDate"] = item["dueDate"]

    bills = sorted(
        [v for v in grouped.values() if v["kind"] == "어음" and v["amount"] != 0],
        key=lambda x: (x["buyerName"], x["buyerCode"]),
    )
    cashes = sorted(
        [v for v in grouped.values() if v["kind"] == "현금" and v["amount"] != 0],
        key=lambda x: (x["buyerName"], x["buyerCode"]),
    )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet2"

    # 열 너비 및 A열 숨김 (기존 양식 동일)
    col_widths = {
        "A": 24.125,
        "B": 9.0,
        "C": 22.625,
        "D": 9.5,
        "E": 17.125,
        "F": 11.625,
        "G": 9.0,
    }
    for col_letter, width in col_widths.items():
        ws.column_dimensions[col_letter].width = width
    ws.column_dimensions["A"].hidden = True

    thin_side = Side(style="thin", color="000000")
    border_thin = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    header_fill = PatternFill(fill_type="solid", start_color="FF0070C0", end_color="FF0070C0")
    summary_fill = PatternFill(fill_type="solid", start_color="FFD9D9D9", end_color="FFD9D9D9")

    font_header = Font(name="맑은 고딕", size=10, bold=True, color="FFFFFFFF")
    font_code_col = Font(name="맑은 고딕", size=10, bold=False, color="FF000000")
    font_data_9 = Font(name="맑은 고딕", size=9, bold=False, color="FF000000")
    font_data_10 = Font(name="맑은 고딕", size=10, bold=False, color="FF000000")
    font_summary_bold = Font(name="맑은 고딕", size=10, bold=True, color="FF000000")
    font_summary_num = Font(name="맑은 고딕", size=10, bold=False, color="FF000000")

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    align_vcenter = Alignment(vertical="center")

    num_fmt_data = '#,##0_);[Red](#,##0)'
    num_fmt_summary = '_-* #,##0_-;\\-* #,##0_-;_-* "-"_-;_-@_-'
    date_fmt = "yyyy-mm-dd"

    # R1 헤더
    headers = ["코드", "매입처", "매입처명", "유형", "예정금액", "어음만기일", "비고"]
    for c_idx, h_text in enumerate(headers, start=1):
        cell = ws.cell(1, c_idx, h_text)
        if c_idx == 1:
            cell.font = font_code_col
            cell.alignment = align_vcenter
        else:
            cell.font = font_header
            cell.fill = header_fill
            cell.alignment = align_center
            cell.border = border_thin
    ws.row_dimensions[1].height = 20

    row_idx = 2

    def write_data_row(r, rec):
        c1 = ws.cell(r, 1, f"{rec['buyerName']}{rec['kind']}")
        c1.font = font_code_col
        c1.alignment = align_vcenter

        c2 = ws.cell(r, 2, str(rec["buyerCode"]))
        c2.font = font_data_9
        c2.alignment = align_center
        c2.border = border_thin

        c3 = ws.cell(r, 3, rec["buyerName"])
        c3.font = font_data_9
        c3.alignment = align_left
        c3.border = border_thin

        c4 = ws.cell(r, 4, rec["kind"])
        c4.font = font_data_10
        c4.alignment = align_center
        c4.border = border_thin

        c5 = ws.cell(r, 5, rec["amount"])
        c5.font = font_data_9
        c5.alignment = align_right
        c5.number_format = num_fmt_data
        c5.border = border_thin

        due_val = None
        if rec["kind"] == "어음" and rec["dueDate"]:
            try:
                due_val = datetime.strptime(rec["dueDate"], "%Y-%m-%d")
            except ValueError:
                due_val = rec["dueDate"]
        c6 = ws.cell(r, 6, due_val)
        c6.font = font_data_9 if rec["kind"] == "어음" else font_data_10
        c6.alignment = align_center
        c6.number_format = date_fmt
        c6.border = border_thin

        c7 = ws.cell(r, 7, None)
        c7.font = font_data_10
        c7.alignment = align_vcenter
        c7.border = border_thin
        ws.row_dimensions[r].height = 17.25

    def write_summary_row(r, label, formula):
        ws.cell(r, 1, None)
        for c_idx in range(2, 8):
            cell = ws.cell(r, c_idx)
            cell.fill = summary_fill
            cell.border = border_thin
            cell.alignment = align_center
            cell.font = font_summary_num

        c4 = ws.cell(r, 4, label)
        c4.font = font_summary_bold
        c4.alignment = align_center

        c5 = ws.cell(r, 5, formula)
        c5.font = font_summary_num
        c5.alignment = align_right
        c5.number_format = num_fmt_summary
        ws.row_dimensions[r].height = 18.5

    # 어음 섹션
    bill_start = row_idx
    for rec in bills:
        write_data_row(row_idx, rec)
        row_idx += 1
    bill_end = row_idx - 1

    bill_summary_row = row_idx
    write_summary_row(
        bill_summary_row,
        "어음 요약",
        f"=SUBTOTAL(9,E{bill_start}:E{bill_end})" if bill_end >= bill_start else 0,
    )
    row_idx += 1

    # 현금 섹션
    cash_start = row_idx
    for rec in cashes:
        write_data_row(row_idx, rec)
        row_idx += 1
    cash_end = row_idx - 1

    cash_summary_row = row_idx
    write_summary_row(
        cash_summary_row,
        "현금 요약",
        f"=SUBTOTAL(9,E{cash_start}:E{cash_end})" if cash_end >= cash_start else 0,
    )
    row_idx += 1

    # 총합계 행 (SUBTOTAL은 내부 SUBTOTAL을 자동 제외하므로 E2:E{cash_summary_row}로 완벽 합산)
    total_row = row_idx
    write_summary_row(total_row, "총합계", f"=SUBTOTAL(9,E2:E{cash_summary_row})")

    # 상단 1행 틀 고정
    ws.freeze_panes = "A2"

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    wb.save(out_path)

    bill_sum = sum(x["amount"] for x in bills)
    cash_sum = sum(x["amount"] for x in cashes)
    return {
        "savedPath": os.path.abspath(out_path),
        "savedName": os.path.basename(out_path),
        "billVendorCount": len(bills),
        "cashVendorCount": len(cashes),
        "billSum": bill_sum,
        "cashSum": cash_sum,
        "totalSum": bill_sum + cash_sum,
    }


def main():
    parser = argparse.ArgumentParser(description="지급품의서 -> 결재집행비교 자동 반영 및 검증")
    parser.add_argument("--proposal", required=True, help="지급품의서 (.xls/.xlsx) 경로")
    parser.add_argument("--comparison", required=True, help="결재집행비교 (.xlsx) 경로")
    parser.add_argument("--vendor-summary-out", default="", help="매입처별 집계표 출력 경로 (.xlsx)")
    parser.add_argument("--no-due-date", action="store_true", help="어음 만기일(I열) 업데이트 생략")
    parser.add_argument("--no-summary", action="store_true", help="집계 시트 소계 업데이트 생략")
    parser.add_argument("--dry-run", action="store_true", help="실제 엑셀 수정 없이 매칭 계획만 미리보기")
    args = parser.parse_args()

    try:
        if not os.path.exists(args.proposal):
            raise FileNotFoundError(f"지급품의서 파일을 찾을 수 없습니다: {args.proposal}")
        if not os.path.exists(args.comparison):
            raise FileNotFoundError(f"결재집행비교 파일을 찾을 수 없습니다: {args.comparison}")

        proposal = parse_proposal_xls(args.proposal)
        comp = analyze_comparison_xlsx(args.comparison)
        matched = match_and_build_plan(proposal, comp)

        plan_data = {
            "targetPath": os.path.abspath(args.comparison),
            "detailSheet": comp["detailSheet"],
            "amountCol": comp["amountCol"],
            "dueDateCol": comp["dueDateCol"],
            "billStartRow": comp["billStartRow"],
            "billSubtotalRow": comp["billSubtotalRow"],
            "cashStartRow": comp["cashStartRow"],
            "cashSubtotalRow": comp["cashSubtotalRow"],
            "totalRow": comp["totalRow"],
            "summarySheet": comp["summarySheet"],
            "summaryBillRow": comp["summaryBillRow"],
            "summaryCashRow": comp["summaryCashRow"],
            "summaryTotalRow": comp["summaryTotalRow"],
            "summaryAmountCol": comp["summaryAmountCol"],
            "updateDueDate": not args.no_due_date,
            "updateSummarySheet": not args.no_summary,
            "updates": matched["updates"],
            "insertBill": matched["insertBill"],
            "insertCash": matched["insertCash"],
        }

        if args.dry_run:
            planned_bill_sum = sum(
                u["amount"] for u in matched["updates"] if u["row"] < comp["billSubtotalRow"]
            ) + sum(x["amount"] for x in matched["insertBill"])
            planned_cash_sum = sum(
                u["amount"] for u in matched["updates"] if u["row"] > comp["billSubtotalRow"]
            ) + sum(x["amount"] for x in matched["insertCash"])

            print(json.dumps({
                "ok": True,
                "dryRun": True,
                "source": {
                    "sheetName": proposal["sheetName"],
                    "cashCount": proposal["cashCount"],
                    "billCount": proposal["billCount"],
                    "cashSum": proposal["cashSum"],
                    "billSum": proposal["billSum"],
                    "totalSum": proposal["totalSum"],
                    "declaredCashSubtotal": proposal["declaredCashSubtotal"],
                    "declaredBillSubtotal": proposal["declaredBillSubtotal"],
                    "declaredTotal": proposal["declaredTotal"],
                },
                "matching": {
                    "updatedRowCount": len(matched["updates"]),
                    "insertedBillCount": len(matched["insertBill"]),
                    "insertedCashCount": len(matched["insertCash"]),
                    "insertedBillItems": matched["insertBill"][:50],
                    "insertedCashItems": matched["insertCash"][:50],
                    "mergedCount": len(matched["mergedLogs"]),
                    "mergedLogs": matched["mergedLogs"][:30],
                    "splitCount": len(matched["splitLogs"]),
                    "splitLogs": matched["splitLogs"][:30],
                },
                "verification": {
                    "plannedBillSum": planned_bill_sum,
                    "plannedCashSum": planned_cash_sum,
                    "plannedTotalSum": planned_bill_sum + planned_cash_sum,
                    "billDiff": planned_bill_sum - proposal["billSum"],
                    "cashDiff": planned_cash_sum - proposal["cashSum"],
                    "totalDiff": (planned_bill_sum + planned_cash_sum) - proposal["totalSum"],
                    "isExactMatch": (
                        planned_bill_sum == proposal["billSum"]
                        and planned_cash_sum == proposal["cashSum"]
                    ),
                },
            }, ensure_ascii=False))
            return

        com_res = run_excel_com(plan_data)
        if not com_res.get("ok"):
            raise RuntimeError(com_res.get("error") or "Excel COM 처리 오류")

        vendor_summary_info = None
        if args.vendor_summary_out:
            vendor_summary_info = generate_vendor_summary_xlsx(proposal, args.vendor_summary_out)

        detail_bill = round(com_res["detailBillSum"])
        detail_cash = round(com_res["detailCashSum"])
        detail_total = round(com_res["detailTotalSum"])

        bill_diff = detail_bill - proposal["billSum"]
        cash_diff = detail_cash - proposal["cashSum"]
        total_diff = detail_total - proposal["totalSum"]

        # XLS 자체 선언 소계와의 차이도 함께 체크
        xls_bill_diff = (
            proposal["billSum"] - proposal["declaredBillSubtotal"]
            if proposal["declaredBillSubtotal"] is not None else 0
        )
        xls_cash_diff = (
            proposal["cashSum"] - proposal["declaredCashSubtotal"]
            if proposal["declaredCashSubtotal"] is not None else 0
        )

        is_exact = (bill_diff == 0 and cash_diff == 0 and total_diff == 0 and xls_bill_diff == 0 and xls_cash_diff == 0)

        print(json.dumps({
            "ok": True,
            "dryRun": False,
            "targetPath": com_res["targetPath"],
            "vendorSummary": vendor_summary_info,
            "source": {
                "sheetName": proposal["sheetName"],
                "cashCount": proposal["cashCount"],
                "billCount": proposal["billCount"],
                "cashSum": proposal["cashSum"],
                "billSum": proposal["billSum"],
                "totalSum": proposal["totalSum"],
                "declaredCashSubtotal": proposal["declaredCashSubtotal"],
                "declaredBillSubtotal": proposal["declaredBillSubtotal"],
                "declaredTotal": proposal["declaredTotal"],
            },
            "matching": {
                "updatedRowCount": len(matched["updates"]),
                "insertedBillCount": len(matched["insertBill"]),
                "insertedCashCount": len(matched["insertCash"]),
                "insertedBillItems": matched["insertBill"],
                "insertedCashItems": matched["insertCash"],
                "mergedCount": len(matched["mergedLogs"]),
                "mergedLogs": matched["mergedLogs"],
                "splitCount": len(matched["splitLogs"]),
                "splitLogs": matched["splitLogs"],
            },
            "result": {
                "detailBillSum": detail_bill,
                "detailCashSum": detail_cash,
                "detailTotalSum": detail_total,
                "summaryBillSum": round(com_res["summaryBillSum"]) if com_res.get("summaryBillSum") is not None else None,
                "summaryCashSum": round(com_res["summaryCashSum"]) if com_res.get("summaryCashSum") is not None else None,
                "summaryTotalSum": round(com_res["summaryTotalSum"]) if com_res.get("summaryTotalSum") is not None else None,
                "finalBillSubtotalRow": com_res["finalBillSubtotalRow"],
                "finalCashSubtotalRow": com_res["finalCashSubtotalRow"],
                "finalTotalRow": com_res["finalTotalRow"],
            },
            "verification": {
                "billDiff": bill_diff,
                "cashDiff": cash_diff,
                "totalDiff": total_diff,
                "xlsBillDiff": xls_bill_diff,
                "xlsCashDiff": xls_cash_diff,
                "isExactMatch": is_exact,
            },
        }, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
