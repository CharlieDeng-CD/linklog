#!/usr/bin/env python3
"""
获取并分析部署日志
"""
import os
import httpx
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

API_BASE_URL = "https://space.ai-builders.com/backend/v1"
API_KEY = os.getenv("AI_BUILDER_TOKEN") or "sk_a5bebbc1_a57c871039be5845359613b5c8d9856cce87"
SERVICE_NAME = "linklog"

def get_logs(log_type="build", stream=None, timeout=60):
    """获取部署日志"""
    url = f"{API_BASE_URL}/deployments/{SERVICE_NAME}/logs"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    params = {
        "log_type": log_type,
        "timeout": timeout
    }
    if stream:
        params["stream"] = stream
    
    print(f"\n{'='*80}")
    print(f"📋 获取 {log_type} 日志" + (f" (stream: {stream})" if stream else ""))
    print(f"{'='*80}\n")
    
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=timeout+10)
        if response.status_code == 200:
            data = response.json()
            logs = data.get("logs", "")
            total_messages = data.get("total_messages", 0)
            
            print(f"✅ 成功获取日志")
            print(f"  └─ 日志类型: {log_type}")
            print(f"  └─ 消息数量: {total_messages}")
            print(f"  └─ 收集时间: {data.get('collected_at', 'N/A')}")
            
            if logs:
                print(f"\n{'='*80}")
                print(f"📄 日志内容:")
                print(f"{'='*80}\n")
                
                lines = logs.split('\n')
                
                # 查找关键信息
                if log_type == "build":
                    # 查找前端构建步骤
                    print("🔍 查找前端构建步骤...")
                    frontend_steps = []
                    build_step_found = False
                    
                    for i, line in enumerate(lines):
                        if 'frontend-builder' in line:
                            frontend_steps.append((i, line))
                            if '7/7' in line or 'RUN npm run build' in line:
                                build_step_found = True
                                print(f"\n✅ 找到构建步骤 (行 {i}):")
                                print(f"  {line}")
                                print(f"\n📋 构建步骤及后续50行:")
                                print('\n'.join(lines[max(0,i-2):min(len(lines),i+50)]))
                                break
                    
                    if not build_step_found:
                        print("⚠️  未找到步骤 7/7 (npm run build)")
                        if frontend_steps:
                            print(f"\n📋 前端构建步骤 ({len(frontend_steps)} 个):")
                            for i, line in frontend_steps[-10:]:
                                print(f"  行 {i}: {line}")
                    
                    # 查找错误信息
                    print(f"\n🔍 查找错误信息...")
                    error_lines = [l for l in lines if any(kw in l.lower() for kw in ['error', 'fail', '❌', 'fatal', 'cannot', 'missing'])]
                    if error_lines:
                        print(f"\n❌ 发现 {len(error_lines)} 个可能的错误:")
                        for line in error_lines[-20:]:
                            print(f"  {line}")
                    else:
                        print("  ℹ️  未发现明显的错误信息")
                
                # 显示最后100行
                print(f"\n{'='*80}")
                print(f"📄 最后100行日志:")
                print(f"{'='*80}\n")
                print('\n'.join(lines[-100:]))
                
            else:
                print("⚠️  日志为空")
                
            return data
        else:
            print(f"❌ 获取日志失败: {response.status_code}")
            print(f"  └─ 响应: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ 获取日志时出错: {str(e)}")
        return None

if __name__ == "__main__":
    import sys
    
    log_type = sys.argv[1] if len(sys.argv) > 1 else "build"
    stream = sys.argv[2] if len(sys.argv) > 2 else None
    
    get_logs(log_type=log_type, stream=stream, timeout=60)

