#!/usr/bin/env python3
"""测试 API 并查看详细日志"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from openai import AsyncOpenAI

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

api_key = os.getenv("AI_BUILDER_TOKEN") or "sk_a5bebbc1_a57c871039be5845359613b5c8d9856cce87"

client = AsyncOpenAI(
    base_url="https://space.ai-builders.com/backend/v1",
    api_key=api_key
)

async def test_init():
    print("="*80)
    print("🧪 测试 /api/v2/init")
    print("="*80)
    
    prompt = """你是一位技术导师专家，擅长将复杂的学习目标分解为清晰的依赖图谱。

用户目标：学习React开发

请生成初始的知识图谱，包含 3-5 个顶层节点（Level 1），这些节点应该是达成目标的核心步骤或主要模块。

**节点分类：**
- goal: 最终目标或子目标
- action: 具体的行动步骤
- prerequisite: 前置知识或必须掌握的技能（这些是用户可能不知道的"未知的未知"）

**重要要求：**
1. 必须识别出至少 1-2 个 prerequisite 节点（用暖色高亮显示）
2. 节点描述要结合用户目标，解释"为什么需要这个"
3. 返回严格的 JSON 格式

**返回格式：**
{
  "nodes": [
    {
      "id": "n1",
      "label": "节点名称",
      "category": "goal|action|prerequisite",
      "description": "一句话描述这个节点"
    }
  ],
  "edges": [
    {
      "source": "n1",
      "target": "n2",
      "reason": "依赖原因"
    }
  ]
}"""
    
    print("\n[System] 📤 发送请求:")
    print(f"   └─ 模型: deepseek")
    print(f"   └─ max_tokens: 1000")
    print(f"   └─ Prompt长度: {len(prompt)} 字符")
    
    import time
    start_time = time.time()
    
    try:
        response = await client.chat.completions.create(
            model="deepseek",
            messages=[
                {
                    "role": "system",
                    "content": "你是一位技术导师专家，擅长识别学习路径中的前置知识和依赖关系。始终返回有效的 JSON 格式。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n[Agent] ✅ AI 响应完成 (耗时: {elapsed_time:.2f}秒)")
        
        # 详细分析响应
        message = response.choices[0].message
        print(f"\n[Agent] 📥 响应详情:")
        print(f"   └─ Finish reason: {message.finish_reason if hasattr(message, 'finish_reason') else 'N/A'}")
        
        # 检查是否有工具调用
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"\n[Agent] 🔧 检测到工具调用！数量: {len(message.tool_calls)}")
            for i, tool_call in enumerate(message.tool_calls, 1):
                print(f"   └─ 工具调用 {i}:")
                print(f"      - ID: {tool_call.id if hasattr(tool_call, 'id') else 'N/A'}")
                print(f"      - Type: {tool_call.type if hasattr(tool_call, 'type') else 'N/A'}")
                if hasattr(tool_call, 'function'):
                    print(f"      - Function: {tool_call.function.name if hasattr(tool_call.function, 'name') else 'N/A'}")
                    args = tool_call.function.arguments if hasattr(tool_call.function, 'arguments') else 'N/A'
                    print(f"      - Arguments: {args[:300] if isinstance(args, str) else args}...")
        else:
            print(f"[Agent] ✅ 无工具调用（纯文本响应）")
        
        content = message.content if message.content else ""
        print(f"\n[Agent] 📄 响应内容:")
        print(f"   └─ 长度: {len(content)} 字符")
        print(f"   └─ 预览: {content[:300]}...")
        
        # Token 使用详情
        if hasattr(response, 'usage'):
            usage = response.usage
            print(f"\n[System] 📊 Token 使用详情:")
            print(f"   └─ Prompt tokens: {usage.prompt_tokens if hasattr(usage, 'prompt_tokens') else 'N/A'}")
            print(f"   └─ Completion tokens: {usage.completion_tokens if hasattr(usage, 'completion_tokens') else 'N/A'}")
            print(f"   └─ Total tokens: {usage.total_tokens if hasattr(usage, 'total_tokens') else 'N/A'}")
            
            # 分析 token 使用
            if hasattr(usage, 'total_tokens') and usage.total_tokens > 1000 * 2:
                print(f"\n[System] ⚠️ 警告：实际使用 tokens ({usage.total_tokens}) 远超设置的 max_tokens (1000)")
                print(f"   └─ 可能原因：")
                print(f"      1. 进行了工具调用（网络搜索等）")
                print(f"      2. API 端忽略了 max_tokens 限制")
                print(f"      3. 模型生成了超长响应")
        else:
            print(f"\n[System] ⚠️ 无 usage 信息")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_init())

