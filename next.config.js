/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  images: { unoptimized: true },
  basePath: '/llm-notes',          // ← 新增
  trailingSlash: true,             // ← 新增,避免 GitHub Pages 路径问题
};

module.exports = nextConfig;