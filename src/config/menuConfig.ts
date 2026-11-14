export interface SubMenuItem {
  id: string;
  title: string;
  path: string;
  badge?: string;
  badgeType?: 'new' | 'settled' | 'modified' | 'critical';
  requiredRole?: ('admin' | 'finance_manager' | 'staff')[];
  description?: string;
}

export interface MenuGroup {
  themeId: string;
  themeTitle: string;
  themeDescription: string;
  iconName: 'Calculator' | 'PieChart' | 'BookOpen' | 'PlusCircle' | 'User';
  dashboard: {
    id: string;
    title: string;
    path: string;
    description: string;
  };
  subMenus: SubMenuItem[];
}

export const THEME_MENU_GROUPS: MenuGroup[] = [
  {
    themeId: 'finance',
    themeTitle: '병원부 정산/재무',
    themeDescription: '병원 제약 공급망 정산 원장 대사 및 미결 금액 관리',
    iconName: 'Calculator',
    dashboard: {
      id: 'finance-dash',
      title: '미결 정산 총괄 대시보드',
      path: '/portal/finance/dashboard',
      description: '월별 예정/실집행액, 미결 잔액 및 병원별 마감 현황 요약',
    },
    subMenus: [
      {
        id: 'reconcile-ledger',
        title: '병원부 미결 통합 원장',
        path: '/portal/finance/reconcile',
        badge: '핵심업무',
        badgeType: 'new',
        description: '거래처별 원장 대사, 수정 및 엑셀 다운로드',
      },
      {
        id: 'variance-analysis',
        title: '월별 차액 분석 현황',
        path: '/portal/finance/variance',
        badge: '신규코딩',
        badgeType: 'modified',
        description: '약정 할인율 대비 집행 차액 모니터링',
      },
    ],
  },
  {
    themeId: 'tools',
    themeTitle: '금융/자산 도구',
    themeDescription: '이자율 시뮬레이션 및 복리 자산 분석',
    iconName: 'PieChart',
    dashboard: {
      id: 'tools-dash',
      title: '금융 시뮬레이션 개요',
      path: '/portal/tools/overview',
      description: '적금 계산기 및 자산 운용 시뮬레이션 허브',
    },
    subMenus: [
      {
        id: 'savings-sim',
        title: '적금/수익 시뮬레이터',
        path: '/portal/tools/simulator',
        badge: '통합됨',
        badgeType: 'settled',
        description: '단리/복리, 과세 유형별 만기 수령액 정밀 계산',
      },
    ],
  },
  {
    themeId: 'knowledge',
    themeTitle: '소통/블로그 허브',
    themeDescription: '사내 공지, 업무 가이드 및 디지털 명함',
    iconName: 'BookOpen',
    dashboard: {
      id: 'blog-hub',
      title: '지식 & 블로그 메인',
      path: '/portal/blog',
      description: '업무 가이드 및 공지사항 실시간 열람',
    },
    subMenus: [
      {
        id: 'blog-list',
        title: '전체 게시글 및 공지',
        path: '/portal/blog',
        description: '카테고리별 업무 지식 아카이브',
      },
      {
        id: 'blog-write',
        title: '새 글 작성하기',
        path: '/portal/blog/write',
        badge: '글쓰기',
        badgeType: 'new',
        requiredRole: ['admin', 'finance_manager'],
        description: '공지사항 및 업무 팁 등록',
      },
      {
        id: 'digital-card',
        title: '디지털 명함 / 소개',
        path: '/portal/profile',
        description: '담당자 프로필 및 연락처 카드',
      },
    ],
  },
  {
    themeId: 'extensible-demo',
    themeTitle: '신규 메뉴 추가 예시',
    themeDescription: '신규 대시보드 및 하위메뉴 그룹화 코딩 템플릿',
    iconName: 'PlusCircle',
    dashboard: {
      id: 'demo-dash',
      title: '신규 대시보드 템플릿',
      path: '/portal/new-menu-demo',
      description: '위젯 및 차트 확장을 위한 표준 대시보드 뷰',
    },
    subMenus: [
      {
        id: 'demo-sub-1',
        title: '신규 하위메뉴 1 (데이터 분석)',
        path: '/portal/new-menu-demo/analytics',
        badge: '템플릿',
        badgeType: 'modified',
        description: '새로운 기능을 코딩하여 등록한 예시',
      },
      {
        id: 'demo-sub-2',
        title: '신규 하위메뉴 2 (관리자 전용)',
        path: '/portal/new-menu-demo/admin-only',
        badge: 'Admin',
        badgeType: 'critical',
        requiredRole: ['admin'],
        description: '관리자 권한(admin)만 접근 가능한 하위메뉴',
      },
    ],
  },
];
