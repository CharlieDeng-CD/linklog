# LinkLog v2 - Dockerfile (简化版用于测试)
# 阶段 1: 构建 Next.js 前端（只保留步骤1-7）
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# 设置环境变量避免并发写入问题
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PRIVATE_STANDALONE=true
ENV NODE_OPTIONS=--max-old-space-size=2048

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装前端依赖（构建需要 devDependencies）
RUN npm ci --legacy-peer-deps

# 复制前端源代码
COPY frontend/ .

# 清理可能的旧构建产物
RUN rm -rf .next out || true

# 测试步骤7：添加调试信息
RUN echo "Step 6 completed successfully"
RUN echo "Starting Step 7: Next.js build preparation..."
RUN pwd
RUN ls -la
RUN echo "Step 7 preparation completed"

# 注意：这里暂时不执行npm run build，先确认步骤7能正常执行
# RUN npm run build

# 阶段 2: Python 后端运行时（简化版）
FROM python:3.11-slim

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
# 注意：由于没有执行npm run build，out目录不存在，这里会失败
# 但我们可以先测试步骤7是否执行，如果步骤7能执行，再恢复完整的构建
# 暂时注释掉这些COPY命令，先测试步骤7
# COPY --from=frontend-builder /app/frontend/out ./frontend/out
# COPY --from=frontend-builder /app/frontend/public ./frontend/public
RUN mkdir -p ./frontend/out ./frontend/public
RUN echo "Skipping COPY from frontend-builder for testing purposes"

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
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD sh -c "python3 -c \"import urllib.request; import os; port=os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/health')\"" || exit 1

# 启动命令（使用 shell 形式以支持环境变量扩展）
CMD sh -c "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"

