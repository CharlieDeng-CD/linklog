#!/bin/sh
# 构建前脚本：从环境变量生成 .env.local 文件
# 这样 Next.js 在构建时就能读取到 NEXT_PUBLIC_* 环境变量

if [ -n "$NEXT_PUBLIC_POSTHOG_KEY" ]; then
  echo "NEXT_PUBLIC_POSTHOG_KEY=$NEXT_PUBLIC_POSTHOG_KEY" > .env.local
  echo "NEXT_PUBLIC_POSTHOG_HOST=${NEXT_PUBLIC_POSTHOG_HOST:-https://app.posthog.com}" >> .env.local
  echo "✅ 已生成 .env.local 文件（包含 PostHog 配置）"
else
  echo "⚠️  NEXT_PUBLIC_POSTHOG_KEY 未设置，跳过 PostHog 配置"
fi
