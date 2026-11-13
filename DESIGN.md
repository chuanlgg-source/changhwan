---
name: Clinical Ledger Precision
stitch_project: projects/12355391550285824806
stitch_design_system: assets/9b621832924a46bab5a483d73b900879
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#444651'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#757682'
  outline-variant: '#c5c5d3'
  surface-tint: '#4059aa'
  primary: '#00236f'
  on-primary: '#ffffff'
  primary-container: '#1e3a8a'
  on-primary-container: '#90a8ff'
  secondary: '#006a61'
  on-secondary: '#ffffff'
  secondary-container: '#86f2e4'
  tertiary: '#442100'
  error: '#ba1a1a'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '700'
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 17px
    fontWeight: '600'
  body-md:
    fontFamily: Noto Sans KR
    fontSize: 13px
    fontWeight: '400'
  num-cell:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    letterSpacing: -0.02em
  num-summary:
    fontFamily: JetBrains Mono
    fontSize: 18px
    fontWeight: '700'
    letterSpacing: -0.03em
---

# Clinical Ledger Precision — Design System

Engineered for hospital pharmaceutical supply chain finance and unsettled discount reconciliation (`병원부 미결 통합 관리 및 리포트 시스템`).

## Key Visual Principles
- **High Information Density without Visual Chaos**: Compact 36px ledger rows, structural hairline dividers (`#E2E8F0` / `#CBD5E1`), and zero ambient shadow in resting states.
- **Rigid Numerical Alignment**: Tabular monospace numerals (`JetBrains Mono`, `font-variant-numeric: tabular-nums`) right-aligned for KRW amounts (`예정금액`, `집행금액`, `미결금액`) and percentages.
- **Semantic Financial Signaling**:
  - **Primary (`#1E3A8A`)**: Deep Cobalt / Navy — Primary controls, active workflow step, active tab indicators.
  - **Settled / Approved (`#059669` on `#ECFDF5`)**: Reconciled / zero-balance (`완결`) states.
  - **Modified / Variance Pending (`#D97706` on `#FFFBEB`)**: Updated rows (`수정됨`) where execution amount or settlement date changed.
  - **New Addition (`#2563EB` on `#EFF6FF`)**: Newly added unsettled records (`신규 추가`) for the selected base month.
  - **Critical Alert (`#DC2626` on `#FEF2F2`)**: Unsettled balance remaining (`미결 잔액`).
