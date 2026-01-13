#!/bin/bash

# LinkLog v2 部署脚本
# 使用方法: ./deploy.sh [环境] [版本]
# 示例: ./deploy.sh production v2

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
ENV=${1:-production}
VERSION=${2:-v2}
PROJECT_NAME="linklog"
CONTAINER_NAME="${PROJECT_NAME}-${VERSION}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🚀 LinkLog ${VERSION} 部署脚本${NC}"
echo -e "${GREEN}========================================${NC}\n"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装，请先安装 Docker${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装，请先安装 Docker Compose${NC}"
    exit 1
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env 文件不存在，从 .env.example 创建...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  请编辑 .env 文件，填入正确的配置${NC}"
        exit 1
    else
        echo -e "${RED}❌ .env.example 文件不存在${NC}"
        exit 1
    fi
fi

# 加载环境变量
source .env

# 检查必要的环境变量
if [ -z "$AI_BUILDER_TOKEN" ]; then
    echo -e "${RED}❌ AI_BUILDER_TOKEN 未设置，请在 .env 文件中配置${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 环境检查通过${NC}\n"

# 停止旧容器（如果存在）
echo -e "${YELLOW}🛑 停止旧容器...${NC}"
docker-compose down ${CONTAINER_NAME} 2>/dev/null || true

# 构建镜像
echo -e "${YELLOW}🔨 构建 Docker 镜像...${NC}"
docker-compose build ${CONTAINER_NAME}

# 启动服务
echo -e "${YELLOW}🚀 启动服务...${NC}"
docker-compose up -d ${CONTAINER_NAME}

# 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 5

# 检查服务状态
if docker ps | grep -q ${CONTAINER_NAME}; then
    echo -e "${GREEN}✅ 容器运行中${NC}"
else
    echo -e "${RED}❌ 容器启动失败${NC}"
    docker-compose logs ${CONTAINER_NAME}
    exit 1
fi

# 健康检查
echo -e "${YELLOW}🏥 健康检查...${NC}"
for i in {1..10}; do
    if curl -s http://localhost:8003/docs > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 服务健康检查通过${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ 健康检查失败，请查看日志${NC}"
        docker-compose logs ${CONTAINER_NAME}
        exit 1
    fi
    sleep 2
done

# 显示部署信息
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}\n"
echo -e "📡 服务地址: ${GREEN}http://localhost:8003${NC}"
echo -e "📚 API 文档: ${GREEN}http://localhost:8003/docs${NC}"
echo -e "📦 容器名称: ${GREEN}${CONTAINER_NAME}${NC}\n"

# 显示容器状态
echo -e "${YELLOW}容器状态:${NC}"
docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "\n${YELLOW}查看日志:${NC}"
echo -e "  docker-compose logs -f ${CONTAINER_NAME}\n"

echo -e "${YELLOW}停止服务:${NC}"
echo -e "  docker-compose stop ${CONTAINER_NAME}\n"

