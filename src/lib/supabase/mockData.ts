export interface BlogPost {
  id: string;
  title: string;
  category: '공지' | '업무가이드' | '정산리포트' | '시스템개선';
  author: string;
  authorRole: string;
  date: string;
  summary: string;
  content: string;
  views: number;
  tags: string[];
}

export const initialBlogPosts: BlogPost[] = [
  {
    id: 'post-local-pc-sync-guide',
    title: '로컬 개발 프로젝트를 다른 PC와 효과적으로 공유·동기화하는 방법',
    category: '업무가이드',
    author: '이창환',
    authorRole: '총괄 매니저',
    date: '2026-11-20',
    summary: '회사 PC와 집 PC 등 여러 컴퓨터를 오가며 개발할 때 GitHub 비공개 저장소를 활용한 표준 동기화 루틴과 .gitignore, 환경 변수(.env), 패키지 관리 주의사항을 정리했습니다.',
    content: `## 1. 가장 추천하는 방법: GitHub(Git) 동기화 루틴
코드는 GitHub에 올리고, 두 PC(예: 회사 PC ↔ 집 PC)가 GitHub를 통해 주고받는 방식입니다. 외부에 공개되면 안 되는 프로젝트라면 Private(비공개) 저장소로 만들면 됩니다.

### 최초 1회 세팅
- PC A (원본 작업 PC): 프로젝트를 GitHub 저장소에 연결하고 첫 업로드(push)
- PC B (다른 PC): 저장소를 통째로 내려받기(clone)
  \`git clone https://github.com/계정명/저장소명.git\`

### 매일 반복하는 동기화 루틴
- 작업 끝낼 때 (PC A): \`git add .\` → \`git commit -m "작업 내용 요약"\` → \`git push\`
- 작업 시작할 때 (PC B): \`git pull\`

---

## 2. 다른 PC로 옮길 때 꼭 챙겨야 할 3가지
1. \`.gitignore\` 설정: \`node_modules/\`, \`.venv/\`, \`dist/\`, \`.env\` 등 용량이 크거나 보안이 필요한 파일 제외
2. 환경 변수(\`.env\`) 및 원본 데이터 별도 공유: 키 이름만 적힌 \`.env.example\`만 GitHub에 올리고, 실제 \`.env\`나 테스트용 엑셀은 구글 드라이브·비밀번호 관리자 등으로 별도 전달
3. 패키지 설치 명령 실행: \`git pull\` 후 \`npm install\` 또는 \`pip install -r requirements.txt\` 실행

---

## 3. 상황별 대안 요약
- 두 PC를 오가며 계속 개발: GitHub Private 저장소 (push / pull) [가장 추천]
- 딱 한 번만 전달: \`node_modules\`, \`.venv\` 제외 후 \`.zip\` 압축 전달
- 오프라인(폐쇄망) 환경: \`git bundle\`로 묶어 USB 이동
- OS/버전 차이 제거: Docker 또는 VS Code Dev Containers`,
    views: 1,
    tags: ['Git', 'GitHub', 'PC동기화', '업무가이드'],
  },
  {
    id: 'post-deploy-workflow-guide',
    title: '개발·배포 워크플로우 3가지 비교 (GitHub 직접 vs 로컬→GitHub vs 구글 드라이브→GitHub)',
    category: '업무가이드',
    author: '이창환',
    authorRole: '총괄 매니저',
    date: '2026-11-20',
    summary: 'GitHub 직접 작성, 로컬 개발 후 GitHub 배포, 구글 드라이브 경유 배포 등 3가지 개발·배포 방식의 장단점을 비교하고 가장 안전하고 효율적인 추천 워크플로우를 정리했습니다.',
    content: `## 1. 깃허브(GitHub)에서 직접 작성하고 배포
- 장점: 별도 개발 환경 세팅 없이 브라우저만으로 작업 및 즉시 커밋·배포 가능
- 단점: 일반 웹 에디터는 실행·디버깅 불가(Codespaces는 무료 한도 제한), 로컬 파일 및 로컬 AI 툴 연동 불편
- 추천도: △ (오타 수정, 문서 편집 등 가벼운 수정용)

---

## 2. 로컬(내 PC)에서 작성하고, 완료되면 깃허브에 올려 배포
- 장점: 가장 빠른 개발·테스트 환경, AI 코딩 툴(Antigravity, VS Code) 최적화, Git 기능 완벽 활용, 검증 후 안전한 배포
- 단점: 최초 1회 로컬 환경 세팅 필요, 미푸시 상태 유실 주의
- 추천도: ★ 가장 추천 (표준 워크플로우)

---

## 3. 구글 드라이브에서 작성하고, 완료되면 깃허브에 올려 배포
- 장점: 자동 클라우드 백업 및 비개발 문서와 함께 관리 가능
- 단점: \`.git\` 폴더 동기화 충돌로 저장소 손상 위험 높음, \`node_modules\` 등 수만 개 파일 동기화로 심각한 속도 저하, 파일 잠금 오류 빈발
- 추천도: ✕ 비추천 (코드 작업 폴더로 사용 금지)

---

## 최종 추천 가이드
1. 기본은 [2번: 로컬 작성 → 깃허브 배포]를 사용하고, 기능 단위·퇴근 전 자주 \`commit\` & \`push\` 하세요.
2. [1번: 깃허브 직접 작성]은 오타 수정·문서 편집 등 가벼운 수정에만 보조로 활용하세요.
3. [3번: 구글 드라이브]는 코드가 아닌 원본 엑셀·기획서·참고 자료 보관용으로만 분리해 사용하세요.`,
    views: 1,
    tags: ['GitHub', '배포가이드', '워크플로우', '업무가이드'],
  },
  {
    id: 'post-1',
    title: '2026년 하반기 병원부 미결 정산 마감 일정 및 유의사항 안내',
    category: '공지',
    author: '이창환',
    authorRole: '총괄 매니저',
    date: '2026-11-10',
    summary: '2026년 하반기 제약 공급망 정산 원장 대사 및 미결 금액 확정을 위한 제출 기한과 전산 반영 절차를 공유합니다.',
    content: `## 1. 정산 마감 개요
병원부 미결 정산 시스템(Clinical Ledger Precision)을 통한 하반기 정산 마감이 진행됩니다.

- **대상 기간**: 2026년 3분기 ~ 4분기 공급 실적
- **1차 마감일**: 2026년 11월 25일 18:00
- **최종 확정일**: 2026년 11월 30일 15:00

---

## 2. 주요 확인 체크리스트
1. **병원별 예정금액 대비 실집행금액 오차율 확인**
   - 차액 발생 건은 [미결 원장 대사] 화면에서 사유 코드 필수 입력
2. **할인율 정산(Discount Reconciliation)**
   - 약정 할인율과 실제 적용 단가 일치 여부 검증
3. **증빙 서류 첨부**
   - 1,000만원 이상 차액 발생 시 증빙 파일 필히 업로드

문의사항은 사내 메신저 또는 댓글로 남겨주시기 바랍니다.`,
    views: 142,
    tags: ['정산마감', '병원부', '공지사항'],
  },
  {
    id: 'post-2',
    title: 'Clinical Ledger Precision 통합 포털 신규 기능 및 메뉴 그룹화 가이드',
    category: '업무가이드',
    author: '시스템관리자',
    authorRole: 'Tech Lead',
    date: '2026-11-12',
    summary: '업무 테마별 GNB 네비게이션과 신규 코딩 페이지를 간편하게 추가하는 메뉴 그룹화 아키텍처 사용 매뉴얼입니다.',
    content: `## 메뉴 그룹화 확장 가이드
본 통합 포털은 모듈형 플러그앤플레이 방식으로 설계되었습니다.

### 신규 하위메뉴 추가 3단계:
1. \`src/app/portal/[도메인]/page.tsx\` 에 새로운 화면 컴포넌트 코딩
2. \`src/config/menuConfig.ts\`의 해당 업무 테마에 항목 등록
\`\`\`typescript
{
  id: 'my-feature',
  title: '신규 분석 화면',
  path: '/portal/finance/analysis',
  badge: 'NEW'
}
\`\`\`
3. 상단 GNB와 좌측 사이드바에 즉시 자동 그룹화되어 반영됩니다!`,
    views: 98,
    tags: ['포털가이드', '신규기능', '메뉴추가'],
  },
  {
    id: 'post-3',
    title: '적금 수익 시뮬레이터 v2.0 연동 및 자산 배분 팁',
    category: '정산리포트',
    author: '이창환',
    authorRole: '총괄 매니저',
    date: '2026-11-14',
    summary: '단리와 복리 시뮬레이션, 비과세 종합저축 한도를 손쉽게 계산할 수 있는 금융 도구가 포털에 통합되었습니다.',
    content: `## 적금 시뮬레이터 활용법
[금융 도구] 테마의 [적금 시뮬레이터] 메뉴를 통해 다양한 이자 계산 옵션을 시뮬레이션할 수 있습니다.

- **원금 분할 불입에 따른 만기 수령액 추정**
- **일반과세(15.4%) vs 세금우대(9.5%) vs 비과세(0%) 비교**
- **월별 누적 이자 그래프 및 차트 분석 기능**

업무 자금 운용 시 참고하시기 바랍니다.`,
    views: 65,
    tags: ['금융도구', '시뮬레이터', '자산관리'],
  },
];
