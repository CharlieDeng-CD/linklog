/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 输出模式：静态导出，由 FastAPI 服务静态文件
  output: 'export',
  // 禁用图片优化（减少构建复杂度）
  images: {
    unoptimized: true,
  },
  // 生产环境不需要 rewrites（API 调用使用完整 URL）
  // 开发环境的 rewrites 只在开发模式下生效
  async rewrites() {
    // 只在开发环境使用 rewrites
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8003/api/:path*',
        },
      ];
    }
    return [];
  },
};

export default nextConfig;

