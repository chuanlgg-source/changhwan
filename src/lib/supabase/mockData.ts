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
