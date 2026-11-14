# Clinical Ledger Precision — 업무 테마별 통합 포털 시스템

병원 제약 공급망 정산, 금융 시뮬레이션, 업무 지식 공유를 아우르는 모던 엔터프라이즈 웹 통합 포털입니다.  
Stitch 디자인 시스템(`Clinical Ledger Precision`)과 Supabase(Auth, PostgreSQL, Storage), Next.js App Router가 결합되어 있습니다.

---

## 🌟 주요 핵심 기능

1. **업무 테마별 통합 공간 (GNB + 동적 LNB)**
   - **병원부 정산/재무**: 미결 정산 대시보드, 미결 원장 대사(`reconcile_ui`), 월별 차액 분석(`variance`)
   - **금융/자산 도구**: 금융 시뮬레이션 대시보드, 적금/수익 시뮬레이터(`savings-simulator`)
   - **소통/블로그 허브**: 업무 지식 블로그(목록, 상세, 작성), 디지털 명함(`profile`)
   - **신규 메뉴 추가 예시**: 모듈형 플러그앤플레이 그룹화 가이드 및 템플릿

2. **로그인 및 권한 제어 (RBAC)**
   - Supabase Auth 기반 실시간 세션 검증
   - 미설정 시 **원클릭 빠른 테스트 계정**(정산 총괄 매니저, 시스템 관리자, 일반 스태프) 내장
   - 역할(`admin`, `finance_manager`, `staff`)에 따른 세부 메뉴 잠금 및 접근 통제

3. **간단한 블로그 페이지**
   - 카테고리 필터(`공지`, `업무가이드`, `정산리포트`, `시스템개선`) 및 검색 기능
   - 마크다운 본문 작성, 자동 태그 분류, 조회수 집계
   - Supabase DB 저장 및 로컬 영속화 동시 지원

4. **Stitch 디자인 시스템 연동 ([DESIGN.md](DESIGN.md))**
   - Deep Cobalt Navy (`#00236f` / `#1e3a8a`), Surface (`#faf8ff`), Hairline Divider
   - 고밀도 수치 정렬 타이포그래피 (`Plus Jakarta Sans`, `Noto Sans KR`, `JetBrains Mono tabular-nums`)
   - 정산 상태 시맨틱 배지 (완결, 수정됨, 신규추가, 미결)

5. **대시보드 및 하위메뉴 신규 코딩 그룹화 방식**
   - 신규 화면을 코딩한 뒤 `src/config/menuConfig.ts`에 항목 1줄만 선언하면 GNB/LNB에 즉시 자동 그룹화

---

## 🚀 빠른 시작 가이드 (Local Development)

### 1. 패키지 설치 및 로컬 서버 구동
```bash
# 개발 서버 실행 (기본 포트: 3000)
npm run dev

# 프로덕션 빌드 및 실행
npm run build
npm start
```

### 2. Supabase 클라우드 연동 (선택 사항)
프로젝트 루트의 `.env.local` 파일에 Supabase 접속 정보를 입력하면 즉시 실제 클라우드 DB와 연동됩니다:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```
> ※ 키를 입력하지 않아도 내장된 **Mock/데모 모드**로 로그인, 블로그 작성 및 모든 대시보드가 정상 작동합니다.  
> ※ DB 테이블 생성은 `supabase/schema.sql`을 Supabase SQL Editor에 복사하여 실행하시면 됩니다.

---

## 🧩 신규 대시보드 & 하위메뉴 추가 3단계

1. **신규 페이지 코딩**:  
   `src/app/portal/[도메인]/page.tsx`에 React 컴포넌트를 코딩합니다.
2. **메뉴 레지스트리 등록**:  
   `src/config/menuConfig.ts`의 원하는 테마에 하위메뉴를 등록합니다:
   ```typescript
   {
     id: 'custom-feature',
     title: '신규 분석 화면',
     path: '/portal/finance/custom-feature',
     badge: 'NEW',
     badgeType: 'new',
     requiredRole: ['finance_manager', 'admin'] // 권한 제어
   }
   ```
3. **완료**:  
   포털 상단 테마 탭과 좌측 사이드바에 즉시 자동 반영됩니다.