import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/config/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Clinical Ledger Precision (Stitch Tokens)
        stitch: {
          surface: '#faf8ff',
          'surface-dim': '#d2d9f4',
          'surface-bright': '#faf8ff',
          'surface-lowest': '#ffffff',
          'surface-low': '#f2f3ff',
          'surface-container': '#eaedff',
          'surface-high': '#e2e7ff',
          'surface-highest': '#dae2fd',
          'on-surface': '#131b2e',
          'on-surface-variant': '#444651',
          'inverse-surface': '#283044',
          'inverse-on-surface': '#eef0ff',
          outline: '#757682',
          'outline-variant': '#c5c5d3',
          'surface-tint': '#4059aa',
          primary: '#00236f',
          'on-primary': '#ffffff',
          'primary-container': '#1e3a8a',
          'on-primary-container': '#90a8ff',
          secondary: '#006a61',
          'on-secondary': '#ffffff',
          'secondary-container': '#86f2e4',
          tertiary: '#442100',
          error: '#ba1a1a',
          // Financial semantic signals
          settled: '#059669',
          'settled-bg': '#ecfdf5',
          modified: '#d97706',
          'modified-bg': '#fffbeb',
          new: '#2563eb',
          'new-bg': '#eff6ff',
          critical: '#dc2626',
          'critical-bg': '#fef2f2',
        },
      },
      fontFamily: {
        headline: ['"Plus Jakarta Sans"', 'sans-serif'],
        sans: ['"Noto Sans KR"', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'stitch-card': '0 1px 3px 0 rgba(0, 35, 111, 0.05), 0 1px 2px -1px rgba(0, 35, 111, 0.05)',
        'stitch-elevated': '0 4px 6px -1px rgba(0, 35, 111, 0.08), 0 2px 4px -2px rgba(0, 35, 111, 0.06)',
      },
    },
  },
  plugins: [],
};
export default config;
