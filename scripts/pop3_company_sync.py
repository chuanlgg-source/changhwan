#!/usr/bin/env python3
"""
회사 POP3(SSL) 메일 3개월 수신함 추출 스크립트
- 서버: mail.geo-young.com
- 포트: 995 (POP3 over SSL)
- 계정: chuanl@geo-young.com

사용 방법:
  python pop3_company_sync.py

실행 후 생성되는 company_emails_3m.json 파일을
포털의 [개인업무 > E-mail 분류(회사) > + 파일 가져오기]에 업로드하세요.
"""

from __future__ import annotations

import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import getpass
import html
import json
import poplib
import re
import ssl
from datetime import datetime, timedelta, timezone

POP3_HOST = "mail.geo-young.com"
POP3_PORT = 995
POP3_USER = "chuanl@geo-young.com"
DAYS = 90
OUTPUT_FILE = "company_emails_3m.json"


def decode_mime_header(raw_value: str | None) -> str:
    if not raw_value:
        return ""
    parts: list[str] = []
    for chunk, charset in decode_header(raw_value):
        if isinstance(chunk, bytes):
            enc = (charset or "utf-8").lower()
            if enc in ("ks_c_5601-1987", "euc-kr", "euc_kr"):
                enc = "cp949"
            try:
                parts.append(chunk.decode(enc, errors="replace"))
            except LookupError:
                parts.append(chunk.decode("utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return "".join(parts).strip()


def extract_text_snippet(msg: email.message.Message, max_len: int = 400) -> str:
    plain_parts: list[str] = []
    html_parts: list[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "").lower()
            if "attachment" in disp:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = (part.get_content_charset() or "utf-8").lower()
            if charset in ("ks_c_5601-1987", "euc-kr", "euc_kr"):
                charset = "cp949"
            try:
                decoded = payload.decode(charset, errors="replace")
            except LookupError:
                decoded = payload.decode("utf-8", errors="replace")

            if ctype == "text/plain":
                plain_parts.append(decoded)
            elif ctype == "text/html":
                html_parts.append(decoded)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = (msg.get_content_charset() or "utf-8").lower()
            if charset in ("ks_c_5601-1987", "euc-kr", "euc_kr"):
                charset = "cp949"
            try:
                decoded = payload.decode(charset, errors="replace")
            except LookupError:
                decoded = payload.decode("utf-8", errors="replace")
            if msg.get_content_type() == "text/html":
                html_parts.append(decoded)
            else:
                plain_parts.append(decoded)

    raw_text = "\n".join(plain_parts).strip()
    if not raw_text and html_parts:
        raw_html = "\n".join(html_parts)
        raw_html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw_html)
        raw_text = re.sub(r"<[^>]+>", " ", raw_html)
        raw_text = html.unescape(raw_text)

    cleaned = re.sub(r"\s+", " ", raw_text).strip()
    return cleaned[:max_len]


def parse_mail_date(raw_date: str | None) -> datetime | None:
    if not raw_date:
        return None
    try:
        dt = parsedate_to_datetime(raw_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
        return dt.astimezone(timezone(timedelta(hours=9)))
    except Exception:
        return None


def main() -> None:
    print(f"POP3 SSL 연결 대상: {POP3_HOST}:{POP3_PORT} ({POP3_USER})")
    password = getpass.getpass("이메일 비밀번호 입력 (화면에 표시되지 않음): ")
    if not password:
        print("비밀번호가 입력되지 않아 종료합니다.")
        return

    ctx = ssl.create_default_context()
    conn = poplib.POP3_SSL(POP3_HOST, POP3_PORT, context=ctx, timeout=30)
    try:
        conn.user(POP3_USER)
        conn.pass_(password)
        count, total_size = conn.stat()
        print(f"접속 성공! 전체 메일 수: {count}건 ({total_size:,} bytes)")

        cutoff = datetime.now(timezone(timedelta(hours=9))) - timedelta(days=DAYS)
        results: list[dict[str, str]] = []
        consecutive_old = 0

        # 최신 메일부터 역순 조회
        for idx in range(count, 0, -1):
            _, lines, _ = conn.top(idx, 0)
            header_bytes = b"\r\n".join(lines)
            hdr_msg = email.message_from_bytes(header_bytes)
            dt = parse_mail_date(hdr_msg.get("Date"))

            if dt is not None and dt < cutoff:
                consecutive_old += 1
                # 최신순 정렬 기준 20건 연속 90일 이전이면 중단
                if consecutive_old >= 20:
                    break
                continue
            consecutive_old = 0

            _, full_lines, _ = conn.retr(idx)
            raw_bytes = b"\r\n".join(full_lines)
            full_msg = email.message_from_bytes(raw_bytes)

            subject = decode_mime_header(full_msg.get("Subject")) or "(제목 없음)"
            sender = decode_mime_header(full_msg.get("From")) or "알 수 없음"
            msg_id = (full_msg.get("Message-ID") or f"pop3_{idx}").strip("<>")
            date_str = dt.strftime("%Y-%m-%d %H:%M") if dt else datetime.now().strftime("%Y-%m-%d %H:%M")
            snippet = extract_text_snippet(full_msg)

            results.append(
                {
                    "id": msg_id,
                    "date": date_str,
                    "sender": sender,
                    "subject": subject,
                    "snippet": snippet,
                    "status": "미처리",
                    "labels": "POP3, GEO-YOUNG",
                }
            )

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"완료! 최근 {DAYS}일 메일 {len(results)}건을 '{OUTPUT_FILE}'에 저장했습니다.")
    finally:
        try:
            conn.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
