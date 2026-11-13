"""
reconcile_server.py — 병원부 미결 통합 관리 및 리포트 웹 서버
Stitch 'Clinical Ledger Precision' 디자인 시스템 기반 대시보드 제공
"""
from __future__ import annotations

import base64
import json
import sys
import tempfile
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

import reconcile_engine as eng

SAMPLE_DIR = BASE_DIR / "sample_data"
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR = Path(tempfile.gettempdir()) / "hospital_reconcile_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────────
# 인메모리 세션 상태 (로드된 4종 데이터 및 최신 분석 결과)
# ──────────────────────────────────────────────────────────────
STATE: dict[str, Any] = {
    "original": None,
    "original_name": "",
    "sahu": None,
    "sahu_name": "",
    "jeoga": None,
    "jeoga_name": "",
    "yakga": None,
    "yakga_name": "",
    "last_analysis": None,
    "last_excel_path": None,
}


def get_available_months() -> list[str]:
    months: set[str] = {
        "2026-12", "2026-11", "2026-10", "2026-09", "2026-08",
        "2026-07", "2026-06", "2026-05", "2026-04", "2026-03",
        "2026-02", "2026-01",
    }
    for key in ("original", "sahu", "jeoga", "yakga"):
        data = STATE.get(key)
        if data and "months" in data:
            for m in data["months"]:
                if m and m >= "2025-01":
                    months.add(m)
    return sorted(months, reverse=True)


def build_status_payload() -> dict[str, Any]:
    orig = STATE["original"]
    sahu = STATE["sahu"]
    jeoga = STATE["jeoga"]
    yakga = STATE["yakga"]
    return {
        "ok": True,
        "available_months": get_available_months(),
        "files": {
            "original": {
                "loaded": orig is not None,
                "filename": STATE.get("original_name", ""),
                "counts": orig["counts"] if orig else {},
                "total": sum(orig["counts"].values()) if orig else 0,
                "months": orig["months"] if orig else [],
            },
            "sahu": {
                "loaded": sahu is not None,
                "filename": STATE.get("sahu_name", ""),
                "count": sahu["count"] if sahu else 0,
                "months": sahu["months"] if sahu else [],
            },
            "jeoga": {
                "loaded": jeoga is not None,
                "filename": STATE.get("jeoga_name", ""),
                "count": jeoga["count"] if jeoga else 0,
                "months": jeoga["months"] if jeoga else [],
            },
            "yakga": {
                "loaded": yakga is not None,
                "filename": STATE.get("yakga_name", ""),
                "count": yakga["count"] if yakga else 0,
                "months": yakga["months"] if yakga else [],
            },
        },
    }


def reset_uploaded_files(step: str = "all") -> dict[str, Any]:
    targets = ("original", "sahu", "jeoga", "yakga") if step == "all" else (step,)
    for k in targets:
        if k in ("original", "sahu", "jeoga", "yakga"):
            STATE[k] = None
            STATE[f"{k}_name"] = ""
    STATE["last_analysis"] = None
    STATE["last_excel_path"] = None
    return build_status_payload()


def preload_sample_files() -> dict[str, Any]:
    s_orig = SAMPLE_DIR / "Sample.xls"
    s_sahu = SAMPLE_DIR / "미결_병원경로_202511-202610.xlsx"
    s_jeoga = SAMPLE_DIR / "병원사후_미결_관리_26년_9월.xlsx"
    s_yakga = SAMPLE_DIR / "약가인하_미결_관리(병원부)S.xls"

    if s_orig.exists():
        STATE["original"] = eng.parse_original_sample(s_orig)
        STATE["original_name"] = s_orig.name
    if s_sahu.exists():
        STATE["sahu"] = eng.parse_sahu_file(s_sahu)
        STATE["sahu_name"] = s_sahu.name
    if s_jeoga.exists():
        STATE["jeoga"] = eng.parse_jeoga_file(s_jeoga)
        STATE["jeoga_name"] = s_jeoga.name
    if s_yakga.exists():
        STATE["yakga"] = eng.parse_yakga_file(s_yakga)
        STATE["yakga_name"] = s_yakga.name

    return build_status_payload()


class ReconcileHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            ui_path = BASE_DIR / "reconcile_ui.html"
            content = ui_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)
            return

        if path == "/api/status":
            self._send_json(build_status_payload())
            return

        if path == "/api/download":
            excel_path = STATE.get("last_excel_path")
            if not excel_path or not Path(excel_path).exists():
                self._send_json({"ok": False, "error": "생성된 엑셀 파일이 없습니다."}, 404)
                return
            p = Path(excel_path)
            data = p.read_bytes()
            encoded_name = urllib.parse.quote(p.name)
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{encoded_name}")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            if path == "/api/preload":
                payload = preload_sample_files()
                self._send_json(payload)
                return

            if path == "/api/reset":
                body = self._read_json_body()
                step = body.get("step", "all")
                payload = reset_uploaded_files(step)
                self._send_json(payload)
                return

            if path == "/api/upload":
                body = self._read_json_body()
                step = body.get("step", "")
                filename = body.get("filename", "uploaded.xlsx")
                b64_data = body.get("content_base64", "")
                if step not in ("original", "sahu", "jeoga", "yakga"):
                    self._send_json({"ok": False, "error": f"잘못된 업로드 단계: {step}"}, 400)
                    return

                ext = Path(filename).suffix.lower()
                if ext not in (".xls", ".xlsx"):
                    self._send_json({"ok": False, "error": "엑셀 파일(.xls 또는 .xlsx)만 업로드 가능합니다."}, 400)
                    return

                raw_bytes = base64.b64decode(b64_data)
                save_path = UPLOAD_DIR / f"{step}_{filename}"
                save_path.write_bytes(raw_bytes)

                if step == "original":
                    STATE["original"] = eng.parse_original_sample(save_path)
                    STATE["original_name"] = filename
                elif step == "sahu":
                    STATE["sahu"] = eng.parse_sahu_file(save_path)
                    STATE["sahu_name"] = filename
                elif step == "jeoga":
                    STATE["jeoga"] = eng.parse_jeoga_file(save_path)
                    STATE["jeoga_name"] = filename
                elif step == "yakga":
                    STATE["yakga"] = eng.parse_yakga_file(save_path)
                    STATE["yakga_name"] = filename

                STATE["last_analysis"] = None
                self._send_json(build_status_payload())
                return

            if path == "/api/analyze":
                body = self._read_json_body()
                base_month = body.get("base_month", "2026-09")

                missing = [
                    label for key, label in [
                        ("original", "Step 2. 원본데이터"),
                        ("sahu", "Step 3-1. 사후미결"),
                        ("jeoga", "Step 3-2. 저가미결"),
                        ("yakga", "Step 3-3. 약가미결"),
                    ]
                    if STATE.get(key) is None
                ]
                if missing:
                    self._send_json({
                        "ok": False,
                        "error": f"다음 스텝의 엑셀 파일을 먼저 업로드해 주세요: {', '.join(missing)}"
                    }, 400)
                    return

                res = eng.analyze_and_merge(
                    STATE["original"],
                    STATE["sahu"],
                    STATE["jeoga"],
                    STATE["yakga"],
                    base_month=base_month,
                )
                STATE["last_analysis"] = res
                self._send_json({"ok": True, "result": res})
                return

            if path == "/api/generate":
                body = self._read_json_body()
                if STATE.get("last_analysis") is None:
                    if all(STATE.get(k) is not None for k in ("original", "sahu", "jeoga", "yakga")):
                        STATE["last_analysis"] = eng.analyze_and_merge(
                            STATE["original"],
                            STATE["sahu"],
                            STATE["jeoga"],
                            STATE["yakga"],
                            base_month=body.get("base_month", "2026-09"),
                        )
                    else:
                        self._send_json({"ok": False, "error": "먼저 2~3스텝 데이터를 업로드하고 분석을 실행해 주세요."}, 400)
                        return

                analysis = STATE["last_analysis"]
                bm = analysis.get("base_month", "2026-09")
                out_name = f"미결(병원부)_통합_{bm}.xlsx"
                out_path = OUTPUT_DIR / out_name
                saved = eng.generate_integrated_excel(analysis, out_path)
                STATE["last_excel_path"] = saved

                self._send_json({
                    "ok": True,
                    "filename": out_name,
                    "saved_path": str(saved),
                    "download_url": "/api/download",
                })
                return

            self.send_error(404)
        except Exception as e:
            traceback.print_exc()
            self._send_json({"ok": False, "error": str(e)}, 500)


def run_server(port: int = 8765, open_browser: bool = True) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), ReconcileHandler)
    url = f"http://127.0.0.1:{port}"
    print(f"[병원부 미결 통합 관리 시스템] 서버 시작: {url}", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    no_browser = "--no-browser" in sys.argv
    run_server(port=p, open_browser=not no_browser)
