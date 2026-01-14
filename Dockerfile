# LinkLog v2 - Dockerfile (多阶段构建)
# 阶段 1: 构建 Next.js 前端
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# 设置环境变量避免并发写入问题
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# 禁用 Next.js 的并发优化，避免写入冲突
ENV NEXT_PRIVATE_STANDALONE=true

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装前端依赖（构建需要 devDependencies）
RUN npm ci --legacy-peer-deps

# 复制前端源代码
COPY frontend/ .

# 构建 Next.js 应用（输出静态文件）
# 清理可能的旧构建产物
RUN rm -rf .next out || true

# 构建（单线程，避免并发写入）
# 增加 Node.js 内存限制以避免构建失败
RUN NODE_OPTIONS="--max-old-space-size=2048" npm run build

# 阶段 2: Python 后端运行时
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 从构建阶段复制前端构建产物（静态导出）
COPY --from=frontend-builder /app/frontend/out ./frontend/out
COPY --from=frontend-builder /app/frontend/public ./frontend/public

# 复制后端代码
COPY server.py .

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 暴露端口（使用 PORT 环境变量，默认 8000）
EXPOSE 8000

# 健康检查（使用 PORT 环境变量）
# 增加启动等待时间，使用 /health 端点
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD sh -c "python3 -c \"import urllib.request; import os; port=os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/health')\"" || exit 1

# 启动命令（使用 shell 形式以支持环境变量扩展）
# PORT 环境变量由 Koyeb 在运行时设置
CMD sh -c "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"
