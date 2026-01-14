#!/bin/bash
# LinkLog 服务器启动脚本（日志输出到终端）

cd "$(dirname "$0")"

# 停止旧进程
if [ -f server.pid ]; then
    OLD_PID=$(cat server.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "停止旧进程 (PID: $OLD_PID)..."
        kill $OLD_PID
        sleep 1
    fi
fi

# 清理端口
lsof -ti:8003 | xargs kill -9 2>/dev/null

# 启动服务（日志输出到终端）
echo "启动 LinkLog 服务器..."
echo "日志将实时显示在此终端中"
echo "按 Ctrl+C 停止服务"
echo ""

python3 server.py

