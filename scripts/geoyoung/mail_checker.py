#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
지오영 병원부 지급집계표 POP3 메일 조회 및 첨부파일 다운로드/파일명 변환 스크립트.
- 표준 라이브러리(poplib, email)만 사용
- 서버의 메일은 절대 삭제(DELE)하지 않고 읽기 전용으로 조회
"""

import argparse
import email
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
import json
import os
import poplib
import re
import ssl
import sys
from datetime import datetime

# UTF-8 stdout 보장
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def decode_mime_str(value):
    if not value:
        return ""
    parts = decode_header(value)
    decoded = []
    for text, charset in parts:
        if isinstance(text, bytes):
            enc = (charset or "utf-8").lower()
            if enc in ("ks_c_5601-1987", "euc-kr", "euc_kr", "cp949", "ms949"):
                enc = "cp949"
            try:
                decoded.append(text.decode(enc, errors="replace"))
            except LookupError:
                decoded.append(text.decode("utf-8", errors="replace"))
        else:
            decoded.append(str(text))
    return "".join(decoded).strip()


def extract_year_month_from_text(text, fallback_dt=None):
    """문자열에서 (YYYY, MM) 추출. 예: 26년11월, 2026.11, (26.11), 2026년 11월"""
    if text:
        m = re.search(r"(20\d{2})\s*[.\-년/]\s*(\d{1,2})\s*월?", text)
        if m:
            return int(m.group(1)), int(m.group(2))
        m = re.search(r"(?<!\d)(\d{2})\s*년\s*(\d{1,2})\s*월", text)
        if m:
            return 2000 + int(m.group(1)), int(m.group(2))
        m = re.search(r"\((\d{2})\.(\d{1,2})\)", text)
        if m:
            return 2000 + int(m.group(1)), int(m.group(2))
    dt = fallback_dt or datetime.now()
    return dt.year, dt.month


def prev_year_month(year, month):
    if month <= 1:
        return year - 1, 12
    return year, month - 1


def classify_attachment(filename):
    """3종 첨부파일 분류: cashflow / comparison / proposal / other"""
    name = filename.strip()
    lower = name.lower()
    if not (lower.endswith(".xlsx") or lower.endswith(".xls")):
        return "other"
    if "월별자금수지계획표" in name:
        return "cashflow"
    if "결재집행비교" in name or "제출비교표" in name:
        return "comparison"
    if "지급품의서" in name:
        return "proposal"
    return "other"


def build_target_filename(kind, orig_name, subject_ym):
    """요구사항에 맞게 파일명 변환"""
    yy, mm = subject_ym
    if kind == "cashflow":
        # 예: 월별자금수지계획표집계(병원부)(26.11).xlsx -> 월별자금수지계획표(병원부)2026.11_예정.xlsx
        fy, fm = extract_year_month_from_text(orig_name, datetime(yy, mm, 1))
        return f"월별자금수지계획표(병원부){fy}.{fm:02d}_예정.xlsx"
    if kind == "comparison":
        # 예: 결재집행비교(병원부_결제시_제출비교표)2026.10^F2026.11.xlsx -> 결재집행비교(병원부_결제시_제출비교표)2026.10~2026.11.xlsx
        matches = re.findall(r"(20\d{2})\.(\d{1,2})", orig_name)
        if len(matches) >= 2:
            y1, m1 = int(matches[0][0]), int(matches[0][1])
            y2, m2 = int(matches[1][0]), int(matches[1][1])
        else:
            y2, m2 = yy, mm
            y1, m1 = prev_year_month(y2, m2)
        return f"결재집행비교(병원부_결제시_제출비교표){y1}.{m1:02d}~{y2}.{m2:02d}.xlsx"
    return orig_name


def connect_pop3(host, port, use_ssl, user, password, timeout=25):
    if use_ssl:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        conn = poplib.POP3_SSL(host, port, timeout=timeout, context=ctx)
    else:
        conn = poplib.POP3(host, port, timeout=timeout)
    conn.user(user)
    conn.pass_(password)
    return conn


def get_uidl_map(conn):
    uidls = {}
    try:
        resp, lines, _ = conn.uidl()
        for line in lines:
            parts = line.decode("ascii", errors="ignore").split()
            if len(parts) >= 2:
                uidls[int(parts[0])] = parts[1]
    except Exception:
        pass
    return uidls


def match_subject(subject, keyword):
    if not keyword:
        return True
    s = re.sub(r"\s+", "", subject or "")
    # 00년00월 같은 패턴이 들어온 경우 유연하게 매칭
    tokens = [t for t in re.split(r"[\s,]+", keyword.strip()) if t]
    for tok in tokens:
        norm_tok = re.sub(r"00년\s*00월", "", tok)
        if norm_tok and norm_tok not in s:
            return False
    return True


def list_matching_mails(conn, sender_filter, subject_keyword, scan_limit=60):
    num_messages, total_size = conn.stat()
    uidl_map = get_uidl_map(conn)
    start_idx = max(1, num_messages - scan_limit + 1)
    matched = []

    for idx in range(num_messages, start_idx - 1, -1):
        try:
            _, lines, _ = conn.top(idx, 0)
        except Exception:
            continue
        raw_hdr = b"\r\n".join(lines)
        msg = email.message_from_bytes(raw_hdr)
        raw_from = decode_mime_str(msg.get("From", ""))
        _, from_addr = parseaddr(raw_from)
        subject = decode_mime_str(msg.get("Subject", ""))
        date_str = msg.get("Date", "")
        msg_id = (msg.get("Message-ID", "") or "").strip()
        uidl = uidl_map.get(idx, msg_id or f"msg-{idx}")

        parsed_dt = None
        iso_date = ""
        try:
            parsed_dt = parsedate_to_datetime(date_str)
            iso_date = parsed_dt.isoformat()
        except Exception:
            iso_date = date_str

        if sender_filter:
            sf = sender_filter.strip().lower()
            if sf not in from_addr.lower() and sf not in raw_from.lower():
                continue
        if not match_subject(subject, subject_keyword):
            continue

        ym = extract_year_month_from_text(subject, parsed_dt)
        matched.append({
            "msgNum": idx,
            "uidl": uidl,
            "messageId": msg_id,
            "from": raw_from,
            "fromAddr": from_addr,
            "subject": subject,
            "date": iso_date,
            "year": ym[0],
            "month": ym[1],
        })

    return {
        "totalMessages": num_messages,
        "scanned": num_messages - start_idx + 1 if num_messages > 0 else 0,
        "matched": matched,
    }


def download_mail_attachments(conn, msg_num, target_dir, work_dir, subject_override=None):
    _, lines, _ = conn.retr(msg_num)
    raw_msg = b"\r\n".join(lines)
    msg = email.message_from_bytes(raw_msg)
    subject = subject_override or decode_mime_str(msg.get("Subject", ""))
    date_str = msg.get("Date", "")
    parsed_dt = None
    try:
        parsed_dt = parsedate_to_datetime(date_str)
    except Exception:
        pass
    subject_ym = extract_year_month_from_text(subject, parsed_dt)

    os.makedirs(target_dir, exist_ok=True)
    os.makedirs(work_dir, exist_ok=True)

    saved = {
        "subject": subject,
        "year": subject_ym[0],
        "month": subject_ym[1],
        "cashflow": None,
        "comparison": None,
        "proposal": None,
        "others": [],
    }

    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        raw_fname = part.get_filename()
        if not raw_fname:
            continue
        fname = decode_mime_str(raw_fname)
        # 경로 구분자 등 안전 문자 제거
        safe_orig = re.sub(r'[\\/:*?"<>|]', "_", fname).strip()
        payload = part.get_payload(decode=True)
        if payload is None:
            continue

        kind = classify_attachment(fname)
        if kind in ("cashflow", "comparison"):
            new_name = build_target_filename(kind, fname, subject_ym)
            dest_path = os.path.join(target_dir, new_name)
            with open(dest_path, "wb") as f:
                f.write(payload)
            # 작업 폴더에도 원본 백업 보관
            backup_path = os.path.join(work_dir, f"orig_{safe_orig}")
            with open(backup_path, "wb") as f:
                f.write(payload)
            saved[kind] = {
                "originalName": fname,
                "savedName": new_name,
                "savedPath": dest_path,
                "backupPath": backup_path,
                "size": len(payload),
            }
        elif kind == "proposal":
            dest_path = os.path.join(work_dir, safe_orig)
            with open(dest_path, "wb") as f:
                f.write(payload)
            saved["proposal"] = {
                "originalName": fname,
                "savedName": safe_orig,
                "savedPath": dest_path,
                "size": len(payload),
            }
        else:
            dest_path = os.path.join(work_dir, safe_orig)
            with open(dest_path, "wb") as f:
                f.write(payload)
            saved["others"].append({
                "originalName": fname,
                "savedPath": dest_path,
                "size": len(payload),
            })

    return saved


def main():
    parser = argparse.ArgumentParser(description="지오영 POP3 메일 조회 및 첨부파일 추출")
    parser.add_argument("--action", choices=["test", "list", "download"], required=True)
    parser.add_argument("--host", default="gw.geo-young.com")
    parser.add_argument("--port", type=int, default=995)
    parser.add_argument("--ssl", action="store_true", default=True)
    parser.add_argument("--no-ssl", dest="ssl", action="store_false")
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", default="")
    parser.add_argument("--sender", default="sky3483@geo-young.com")
    parser.add_argument("--subject", default="지오영병원부 지급집계표")
    parser.add_argument("--scan-limit", type=int, default=60)
    parser.add_argument("--msg-num", type=int, default=0)
    parser.add_argument("--target-dir", default=r"E:\OneDrive\업무\지오영_지불결의서_집계표")
    parser.add_argument("--work-dir", default="")
    args = parser.parse_args()

    password = args.password or os.environ.get("GEOYOUNG_MAIL_PASSWORD", "")
    if not password:
        print(json.dumps({"ok": False, "error": "이메일 비밀번호가 설정되지 않았습니다."}, ensure_ascii=False))
        sys.exit(1)

    conn = None
    try:
        conn = connect_pop3(args.host, args.port, args.ssl, args.user, password)
        if args.action == "test":
            count, size = conn.stat()
            print(json.dumps({
                "ok": True,
                "message": f"POP3 연결 성공 (총 {count}통, {size:,} bytes)",
                "totalMessages": count,
                "mailboxBytes": size,
            }, ensure_ascii=False))
        elif args.action == "list":
            res = list_matching_mails(conn, args.sender, args.subject, args.scan_limit)
            print(json.dumps({"ok": True, **res}, ensure_ascii=False))
        elif args.action == "download":
            if args.msg_num <= 0:
                raise ValueError("--msg-num이 필요합니다.")
            work_dir = args.work_dir or os.path.join(args.target_dir, "_mail_work")
            res = download_mail_attachments(conn, args.msg_num, args.target_dir, work_dir)
            print(json.dumps({"ok": True, **res}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
    finally:
        if conn is not None:
            try:
                conn.quit()
            except Exception:
                pass


if __name__ == "__main__":
    main()
