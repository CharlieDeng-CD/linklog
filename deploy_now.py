#!/usr/bin/env python3
"""
LinkLog 部署脚本
通过 ai-builders-coach API 部署到 ai-builders.space
"""
import httpx
import os
import json
import sys

# 从环境变量获取 token
token = os.getenv('AI_BUILDER_TOKEN', 'sk_a5bebbc1_a57c871039be5845359613b5c8d9856cce87')

# 部署 API 端点
url = 'https://space.ai-builders.com/backend/v1/deployments'

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# 部署请求数据
payload = {
    'repo_url': 'https://github.com/CharlieDeng-CD/linklog',
    'service_name': 'linklog',
    'branch': 'main',  # 先尝试 main，如果失败再试 master
    'port': 8000
}

print('🚀 开始部署 LinkLog...')
print(f'📦 仓库: {payload["repo_url"]}')
print(f'🏷️  服务名称: {payload["service_name"]}')
print(f'🌿 分支: {payload["branch"]}')
print(f'🔌 端口: {payload["port"]}')
print()

try:
    response = httpx.post(url, json=payload, headers=headers, timeout=120.0)
    print(f'📡 响应状态码: {response.status_code}')
    
    if response.status_code == 202:
        data = response.json()
        print('✅ 部署请求已提交！')
        print()
        print(f'📋 部署信息:')
        print(f'   服务名称: {data.get("service_name", "N/A")}')
        print(f'   状态: {data.get("status", "N/A")}')
        print(f'   消息: {data.get("message", "N/A")}')
        if data.get('public_url'):
            print(f'   🌐 公网地址: {data.get("public_url")}')
        print()
        if data.get('streaming_logs'):
            print('📝 构建日志（前500字符）:')
            logs = data.get('streaming_logs', '')
            print(logs[:500] + '...' if len(logs) > 500 else logs)
        print()
        print('💡 提示:')
        print('   - 部署通常需要 5-10 分钟')
        print('   - 可以通过以下命令查看部署状态:')
        print(f'     curl -H "Authorization: Bearer $AI_BUILDER_TOKEN" \\')
        print(f'          https://space.ai-builders.com/backend/v1/deployments/{payload["service_name"]}')
    else:
        print(f'❌ 部署失败: {response.status_code}')
        print(f'响应内容: {response.text}')
        sys.exit(1)
except Exception as e:
    print(f'❌ 错误: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

