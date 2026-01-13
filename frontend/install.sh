#!/bin/bash

echo "🚀 开始安装 LinkLog 前端依赖..."
echo ""
echo "📦 使用镜像源: $(npm config get registry)"
echo ""

# 安装依赖并显示进度
npm install --progress=true --loglevel=info

echo ""
if [ $? -eq 0 ]; then
    echo "✅ 依赖安装完成！"
    echo ""
    echo "下一步："
    echo "  npm run dev"
else
    echo "❌ 安装失败，请检查网络连接"
fi

