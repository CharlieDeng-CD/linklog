#!/usr/bin/env python3
"""
使用 AI Builders API 部署 LinkLog 服务
"""
import os
import json
import httpx
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# API 配置
API_BASE_URL = "https://space.ai-builders.com/backend/v1"
API_KEY = os.getenv("AI_BUILDER_TOKEN") or "sk_a5bebbc1_a57c871039be5845359613b5c8d9856cce87"

if not API_KEY:
    raise ValueError("AI_BUILDER_TOKEN 未设置，请检查 .env 文件")

# 读取部署配置
config_path = Path(__file__).parent.parent / "deploy-config.json"
with open(config_path, 'r') as f:
    config = json.load(f)

def deploy():
    """执行部署"""
    print("="*80)
    print("🚀 开始部署 LinkLog 服务")
    print("="*80)
    print(f"\n📋 部署配置:")
    print(f"  └─ 服务名称: {config['service_name']}")
    print(f"  └─ 仓库 URL: {config['repo_url']}")
    print(f"  └─ 分支: {config['branch']}")
    print(f"  └─ 端口: {config['port']}")
    print(f"  └─ 环境变量: {len(config.get('env_vars', {}))} 个")
    
    # 准备请求
    url = f"{API_BASE_URL}/deployments"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "repo_url": config["repo_url"],
        "service_name": config["service_name"],
        "branch": config["branch"],
        "port": config["port"]
    }
    
    # 如果有环境变量，添加到 payload
    if config.get("env_vars"):
        payload["env_vars"] = config["env_vars"]
    
    print(f"\n📤 发送部署请求...")
    print(f"  └─ API URL: {url}")
    
    # 重试机制
    max_retries = 3
    retry_delay = 5  # 秒
    
    for attempt in range(max_retries):
        try:
            print(f"\n📤 发送部署请求... (尝试 {attempt + 1}/{max_retries})")
            print(f"  └─ API URL: {url}")
            
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload, headers=headers)
                
                print(f"\n📥 响应状态: {response.status_code}")
                
                if response.status_code == 202:
                    result = response.json()
                    print(f"\n✅ 部署已排队")
                    print(f"  └─ 服务名称: {result.get('service_name')}")
                    print(f"  └─ 状态: {result.get('status')}")
                    print(f"  └─ 公共 URL: {result.get('public_url', 'N/A')}")
                    
                    if result.get('streaming_logs'):
                        print(f"\n📋 初始构建日志:")
                        print("-" * 80)
                        print(result['streaming_logs'])
                        print("-" * 80)
                    
                    if result.get('message'):
                        print(f"\n💡 提示:")
                        print(f"  {result['message']}")
                    
                    print(f"\n⏱️  部署通常需要 5-10 分钟")
                    print(f"📊 查看状态: GET {API_BASE_URL}/deployments/{config['service_name']}")
                    print(f"📋 查看日志: GET {API_BASE_URL}/deployments/{config['service_name']}/logs")
                    
                    return result
                elif response.status_code in [502, 503, 504]:
                    # 服务器错误，重试
                    if attempt < max_retries - 1:
                        error_text = response.text[:200]
                        print(f"\n⚠️  服务器错误 ({response.status_code})，{retry_delay}秒后重试...")
                        print(f"  └─ 错误信息: {error_text}")
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        error_text = response.text
                        print(f"\n❌ 部署失败（服务器错误）")
                        print(f"  └─ 状态码: {response.status_code}")
                        print(f"  └─ 错误信息: {error_text[:500]}")
                        raise Exception(f"部署失败: {response.status_code} - 服务器暂时不可用，请稍后重试")
                else:
                    error_text = response.text
                    print(f"\n❌ 部署失败")
                    print(f"  └─ 状态码: {response.status_code}")
                    print(f"  └─ 错误信息: {error_text[:500]}")
                    raise Exception(f"部署失败: {response.status_code} - {error_text[:200]}")
                    
        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                print(f"\n⚠️  请求超时，{retry_delay}秒后重试...")
                import time
                time.sleep(retry_delay)
                continue
            else:
                raise Exception("部署请求超时，请稍后重试")
        except Exception as e:
            if attempt < max_retries - 1 and "502" in str(e) or "503" in str(e) or "504" in str(e):
                print(f"\n⚠️  连接错误，{retry_delay}秒后重试...")
                import time
                time.sleep(retry_delay)
                continue
            else:
                print(f"\n❌ 部署过程中出错: {str(e)}")
                raise

if __name__ == "__main__":
    deploy()

