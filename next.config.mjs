/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // iframe이나 기존 static html 파일들을 /legacy/ 로 직접 서빙할 수 있도록 rewrite 또는 public 제공
};

export default nextConfig;
