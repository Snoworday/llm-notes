/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',           // ← 新增,启用静态导出
  images: { unoptimized: true }, // ← 新增,避免图片优化报错
};

module.exports = nextConfig;