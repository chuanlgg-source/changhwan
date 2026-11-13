@echo off
chcp 65001 > nul
title 병원부 미결 통합 관리 및 리포트 시스템
echo [병원부 미결 통합 관리 및 리포트 시스템] 웹 대시보드를 시작합니다...
echo 브라우저가 자동으로 열립니다 (http://127.0.0.1:8765)
"C:\Users\chuan\AppData\Local\Programs\Python\Python312\python.exe" "%~dp0reconcile_server.py" 8765
