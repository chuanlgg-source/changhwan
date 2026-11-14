# Clinical Ledger Precision — 업무 테마별 통합 포털 시스템

병원 제약 공급망 정산, 금융 시뮬레이션, 업무 지식 공유를 아우르는 모던 엔터프라이즈 웹 통합 포털입니다.  
Stitch 디자인 시스템(`Clinical Ledger Precision`), Supabase(PostgreSQL & Auth), 그리고 **AI 프롬프트 연동형 단일 스펙(SSOT)** 아키텍처가 결합되어 있습니다.

* **라이브 서비스 URL**: [https://chuanlgg-source.github.io/changhwan/](https://chuanlgg-source.github.io/changhwan/)

---

## 🌟 주요 핵심 기능

1. **업무 테마별 통합 공간 (GNB + 동적 LNB)**
   - **🏥 병원부 정산/재무**: 미결 정산 대시보드, 미결 원장 대사(`reconcile_ui.html`), 월별 차액 소명 관리(`variance`)
   - **📊 금융/자산 도구**: 금융 시뮬레이션 대시보드, 적금/수익 시뮬레이터(`savings-simulator.html`)
   - **📖 소통/블로그 허브**: 업무 지식 블로그(목록, 상세, 작성), 디지털 명함(`business-card.html`)
   - **⚙️ 내부관리 (관리자 전용)**: 업무 계정 및 비밀번호 관리, 메뉴 그룹화, Supabase 연동 관리

2. **업무 이메일 및 비밀번호 계정 관리 (내부관리 분리)**
   - 신규 임직원 업무 이메일 발급 및 비밀번호 설정
   - 관리자용 비밀번호 재설정 및 계정 잠금(비활성화) 제어
   - 임직원 본인 비밀번호 변경 모달 기본 제공

3. **Stitch 디자인 시스템 연동 ([DESIGN.md](DESIGN.md))**
   - Deep Cobalt Navy (`#00236f` / `#1e3a8a`), Surface (`#faf8ff`), Hairline Divider
   - 고밀도 수치 정렬 타이포그래피 (`Plus Jakarta Sans`, `Noto Sans KR`, `JetBrains Mono tabular-nums`)
   - 정산 상태 시맨틱 배지 (완결, 수정됨, 신규추가, 미결)

---

## 🤖 AI 프롬프트 연동 메뉴 관리 워크플로우 (방안 1)

본 포털은 UI에서 수동으로 입력할 필요 없이, **채팅창에서 자연어 프롬프트만으로 일관성 있게 메뉴를 생성, 수정, 삭제**할 수 있도록 단일 진실 원천(SSOT) 스펙 체계를 갖추고 있습니다.

* **메뉴 마스터 스펙**: [`portal-spec.json`](portal-spec.json)
* **AI 엔지니어링 가이드라인**: [`PORTAL_RULES.md`](PORTAL_RULES.md)

### 💬 프롬프트 요청 예시
채팅창에 아래와 같이 지시하시면 AI가 규칙에 맞춰 `portal-spec.json` 갱신 및 신규 페이지 코딩 후 즉시 배포합니다:
* *"병원부 정산 테마 하위에 '의약품 반품 정산' 메뉴를 추가하고 샘플 테이블 페이지를 만들어줘."*
* *"'월별 미결 차액 소명 관리' 메뉴를 내부관리자(Admin) 전용 메뉴로 변경해줘."*
* *"'신규 메뉴 확장 샘플' 테마에서 특정 메뉴를 삭제해줘."*

---

## 🚀 파일 및 인프라 구조
* `index.html`: 통합 포털 메인 애플리케이션 (GitHub Pages 라이브 배포)
* `portal-spec.json`: 전체 테마 및 메뉴 계층 구조 명세 (SSOT)
* `PORTAL_RULES.md`: AI 프롬프트 연동 규칙 및 Stitch 디자인 가이드
* `reconcile_ui.html` & `reconcile_engine.py`: 병원부 미결 원장 대사 엔진
* `savings-simulator.html`: 적금 및 수익률 정밀 시뮬레이터
* `business-card.html`: 이창환 총괄 매니저 디지털 명함
* `template-page.html`: 신규 코딩용 표준 HTML 템플릿
* `supabase/schema.sql`: Supabase PostgreSQL 테이블 및 RLS 스크립트