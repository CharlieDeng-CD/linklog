"""
LinkLog - 后端服务器
提供多源课程解析、知识图谱生成等 API
"""
import os
import json
import re
import httpx
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import AsyncOpenAI
from openai import APIError
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import asyncio
import time

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# 版本信息
VERSION = os.getenv("VERSION", "v2.0.0")
PORT = int(os.getenv("PORT", "8000"))  # 统一使用 8000，与 Dockerfile 一致

app = FastAPI(
    title="LinkLog API",
    version=VERSION,
    description="渐进式知识图谱生成器 API"
)

# 启用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 OpenAI 异步客户端（支持并发请求）
# 优先从环境变量读取，如果没有则使用默认密钥（仅用于开发）
api_key = os.getenv("AI_BUILDER_TOKEN") or "sk_a5bebbc1_a57c871039be5845359613b5c8d9856cce87"

client = AsyncOpenAI(
    base_url="https://space.ai-builders.com/backend/v1",
    api_key=api_key
)

print(f"✓ OpenAI 客户端已初始化")
print(f"  Base URL: https://space.ai-builders.com/backend/v1")
print(f"  API Key: {api_key[:20]}...")

# 静态文件目录（v1 版本）
static_dir = Path(__file__).parent / "static"

# Next.js 构建目录（v2 版本 - 静态导出）
frontend_out_dir = Path(__file__).parent / "frontend" / "out"
frontend_public_dir = Path(__file__).parent / "frontend" / "public"

# 挂载静态文件（必须在路由之前）
# 优先挂载 Next.js 构建产物（v2 - 静态导出）
if frontend_out_dir.exists():
    # 挂载 Next.js 静态导出目录
    app.mount("/_next", StaticFiles(directory=str(frontend_out_dir / "_next")), name="next-static")
    # 挂载公共资源
    if frontend_public_dir.exists():
        app.mount("/public", StaticFiles(directory=str(frontend_public_dir)), name="public")
    print(f"✓ Next.js 静态文件已挂载")
    print(f"  - 导出目录: {frontend_out_dir}")
    print(f"  - 公共目录: {frontend_public_dir}")

# v1 版本的静态文件（向后兼容）
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    print(f"✓ v1 静态文件目录已挂载: {static_dir}")
else:
    print(f"⚠ 警告: v1 静态文件目录不存在: {static_dir}")

# ==================== 数据模型 ====================

class URLInput(BaseModel):
    """URL 输入模型"""
    url: str

class TextInput(BaseModel):
    """文本输入模型"""
    text: str

class AnalyzeRequest(BaseModel):
    """分析请求模型"""
    urls: List[str] = []
    texts: List[str] = []


# ==================== 工具函数 ====================

def fix_json_string(json_str: str) -> str:
    """
    修复常见的 JSON 格式问题
    
    处理的问题：
    1. 移除尾随逗号
    2. 修复未闭合的字符串（添加闭合引号）
    3. 转义字符串中的换行符
    4. 修复未转义的引号
    """
    # 移除尾随逗号（在对象或数组的最后一个元素后）
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    # 修复未闭合的字符串字段值
    # 匹配模式：字段名: "值（可能跨多行，未闭合）
    # 例如："description": "使用 HTML/CSS/JS 或框架构建博客外观，确保在手机和电脑上
    pattern = r'("(?:description|label|reason|summary|context|definition|action)":\s*")([^"]*(?:\n[^"]*)*?)(?=\s*[,}\]]|$)'
    
    def fix_field(match):
        field_name = match.group(1)
        field_value = match.group(2)
        # 转义换行符和回车符
        field_value = field_value.replace('\n', '\\n').replace('\r', '\\r')
        # 移除末尾的空白字符
        field_value = field_value.rstrip()
        return field_name + field_value + '"'
    
    # 从后往前处理匹配，避免位置偏移问题
    matches = list(re.finditer(pattern, json_str, re.MULTILINE | re.DOTALL))
    for match in reversed(matches):
        start, end = match.span()
        # 检查这个匹配后面是否有闭合引号
        after_match = json_str[end:end+10].strip()
        # 如果后面没有引号，说明字符串未闭合
        if not after_match.startswith('"'):
            # 检查后面是否有逗号、}、]等
            next_char = after_match[0] if after_match else ''
            if next_char in [',', '}', ']', '\n']:
                # 修复这个字段
                fixed = fix_field(match)
                json_str = json_str[:start] + fixed + json_str[end:]
    
    return json_str


def parse_json_with_fallback(content: str) -> dict:
    """
    解析 JSON，带多层回退机制
    
    1. 尝试直接解析
    2. 尝试修复后解析
    3. 尝试提取 JSON 对象
    4. 尝试部分提取数据
    """
    original_content = content
    
    # 步骤 1: 提取 JSON 代码块（如果有）
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        parts = content.split("```")
        if len(parts) >= 3:
            content = parts[1].strip()
            if content.startswith("json"):
                content = content[4:].strip()
    
    # 步骤 2: 尝试直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"   └─ JSON 直接解析失败: {e.msg} at line {e.lineno}, column {e.colno}")
    
    # 步骤 3: 尝试修复后解析
    try:
        fixed_content = fix_json_string(content)
        return json.loads(fixed_content)
    except json.JSONDecodeError as e:
        print(f"   └─ JSON 修复后解析失败: {e.msg} at line {e.lineno}, column {e.colno}")
    
    # 步骤 4: 尝试提取完整的 JSON 对象（使用正则）
    try:
        # 查找第一个 { 到最后一个 } 之间的内容
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            extracted_json = json_match.group(0)
            extracted_json = fix_json_string(extracted_json)
            return json.loads(extracted_json)
    except Exception as e:
        print(f"   └─ 正则提取 JSON 失败: {str(e)}")
    
    # 步骤 5: 尝试部分提取数据
    print("   └─ 尝试部分提取数据...")
    result = {
        "nodes": [],
        "edges": [],
        "summary": "JSON 解析失败，已提取部分数据"
    }
    
    # 提取节点
    node_pattern = r'"id"\s*:\s*"([^"]+)"\s*,\s*"label"\s*:\s*"([^"]*?)"(?:"|(?:\s*,\s*"category"|\s*,\s*"type"|\s*\}))'
    nodes = re.findall(node_pattern, content, re.DOTALL)
    for i, (node_id, label) in enumerate(nodes[:20]):
        # 清理 label（移除换行和多余空格）
        label = label.replace('\n', ' ').replace('\r', '').strip()
        if label:
            result["nodes"].append({
                "id": node_id if node_id else f"n{i+1}",
                "label": label,
                "category": "action",  # 默认值
                "description": ""
            })
    
    # 提取边
    edge_pattern = r'"source"\s*:\s*"([^"]+)"\s*,\s*"target"\s*:\s*"([^"]+)"'
    edges = re.findall(edge_pattern, content)
    for source, target in edges[:20]:
        result["edges"].append({
            "source": source,
            "target": target,
            "reason": ""
        })
    
    print(f"   └─ 部分提取完成: {len(result['nodes'])} 个节点, {len(result['edges'])} 条边")
    return result


def log_ai_request(
    endpoint_name: str,
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int
):
    """
    详细打印 AI API 请求信息（用于 Token 消耗分析）
    """
    print("\n" + "="*100)
    print(f"🤖 AI API 请求 - {endpoint_name}")
    print("="*100)
    
    # 计算字符数和估算token数（粗略估算：1 token ≈ 4 字符）
    system_chars = len(system_prompt)
    user_chars = len(user_prompt)
    total_chars = system_chars + user_chars
    
    system_tokens_est = system_chars // 4
    user_tokens_est = user_chars // 4
    total_tokens_est = total_chars // 4
    
    print(f"\n📊 请求统计:")
    print(f"  └─ 模型: {model}")
    print(f"  └─ 温度: {temperature}")
    print(f"  └─ 最大输出Token: {max_tokens}")
    print(f"  └─ System Prompt 长度: {system_chars:,} 字符 (~{system_tokens_est:,} tokens)")
    print(f"  └─ User Prompt 长度: {user_chars:,} 字符 (~{user_tokens_est:,} tokens)")
    print(f"  └─ 总输入长度: {total_chars:,} 字符 (~{total_tokens_est:,} tokens)")
    
    print(f"\n📝 System Prompt (完整内容):")
    print("-" * 100)
    print(system_prompt)
    print("-" * 100)
    
    print(f"\n📝 User Prompt (完整内容):")
    print("-" * 100)
    # 如果User Prompt太长，只显示前2000字符和最后500字符
    if user_chars > 2500:
        print(user_prompt[:2000])
        print("\n... [中间内容已省略] ...\n")
        print(user_prompt[-500:])
        print(f"\n⚠️  提示: User Prompt 总长度 {user_chars:,} 字符，已省略中间部分")
    else:
        print(user_prompt)
    print("-" * 100)
    print("="*100 + "\n")


async def call_ai_with_retry(
    client: AsyncOpenAI,
    model: str,
    messages: List[Dict],
    temperature: float,
    max_tokens: int,
    max_retries: int = 3,
    retry_delay: float = 2.0,
    fallback_models: List[str] = None,
    disable_tools: bool = True
):
    """
    带重试机制和备用模型的 AI API 调用
    
    Args:
        client: OpenAI 客户端
        model: 首选模型名称（如果为 "deepseek" 且不可用，会自动跳过）
        messages: 消息列表
        temperature: 温度参数
        max_tokens: 最大token数
        max_retries: 每个模型的最大重试次数
        retry_delay: 重试延迟（秒）
        fallback_models: 备用模型列表（如果主模型失败，会尝试这些模型）
        disable_tools: 是否禁用工具调用（避免token激增）
    
    Returns:
        API 响应对象
    """
    # 默认备用模型列表（优先使用 grok-4-fast，因为它不会自动进行工具调用）
    if fallback_models is None:
        fallback_models = ["grok-4-fast", "gemini-3-flash-preview"]
    
    # 如果主模型是 deepseek，直接跳过（因为完全不可用）
    if model == "deepseek":
        print(f"[System] ⚠️  deepseek 模型不可用，直接使用备用模型")
        models_to_try = fallback_models
    else:
        # 尝试的模型列表：首选模型 + 备用模型
        models_to_try = [model] + fallback_models
    
    for model_to_use in models_to_try:
        print(f"\n[System] 🔄 尝试使用模型: {model_to_use}")
        
        for attempt in range(max_retries):
            try:
                # 构建API调用参数
                api_params = {
                    "model": model_to_use,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                # 禁用工具调用（避免token激增）
                # 注意：某些模型（如grok-4-fast）不支持同时设置 tools=None 和 tool_choice
                # 所以我们只设置 tools=None，不设置 tool_choice
                if disable_tools:
                    # 不传 tools 和 tool_choice 参数，让模型默认不使用工具
                    pass  # 不设置任何工具相关参数即可禁用工具调用
                
                response = await client.chat.completions.create(**api_params)
                
                if model_to_use != model:
                    print(f"[System] ✅ 备用模型 {model_to_use} 调用成功")
                return response
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                # 尝试从异常中提取状态码
                status_code = None
                if hasattr(e, 'status_code'):
                    status_code = e.status_code
                elif hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                    status_code = e.response.status_code
                elif hasattr(e, 'code'):
                    status_code = e.code
                
                # 检查是否是服务器错误（502, 503, 504）或网络错误
                is_server_error = (
                    status_code in [502, 503, 504] or
                    "502" in error_msg or 
                    "503" in error_msg or 
                    "504" in error_msg or
                    "Bad Gateway" in error_msg or
                    "Service Unavailable" in error_msg or
                    "Gateway Timeout" in error_msg or
                    "InternalServerError" in str(type(e).__name__)
                )
                
                if is_server_error:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)  # 指数退避
                        print(f"\n[System] ⚠️  API 服务器错误 (模型: {model_to_use}, 状态码: {status_code}, 错误: {error_msg[:100]}...)，{wait_time:.1f}秒后重试 (尝试 {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # 当前模型重试失败，尝试下一个备用模型
                        print(f"\n[System] ⚠️  模型 {model_to_use} 重试 {max_retries} 次后仍然失败，尝试备用模型...")
                        break  # 跳出当前模型的重试循环，尝试下一个模型
                else:
                    # 其他错误（如认证错误、参数错误等），如果是第一个模型，尝试备用模型；否则直接抛出
                    if model_to_use == model and len(models_to_try) > 1:
                        print(f"\n[System] ⚠️  模型 {model_to_use} 遇到非服务器错误: {error_msg[:200]}，尝试备用模型...")
                        break  # 尝试备用模型
                    else:
                        print(f"\n[System] ❌ API 错误: {error_msg[:200]}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"AI API 调用失败: {error_msg[:200]}"
                        )
        else:
            # 如果当前模型的所有重试都成功完成（没有break），说明已经返回了响应
            continue
        
        # 如果执行到这里，说明当前模型失败了，继续尝试下一个模型
        continue
    
    # 如果所有模型都失败了
    raise HTTPException(
        status_code=503,
        detail=f"AI 服务暂时不可用。已尝试 {len(models_to_try)} 个模型，每个模型重试 {max_retries} 次，请稍后再试。如果问题持续，请联系服务提供商。"
    )


def log_ai_response(
    endpoint_name: str,
    response_content: str,
    usage: Optional[object] = None,
    show_full_response: bool = False
):
    """
    详细打印 AI API 响应信息（用于 Token 消耗分析）
    """
    print("\n" + "="*100)
    print(f"✅ AI API 响应 - {endpoint_name}")
    print("="*100)
    
    # Token 使用详情
    if usage:
        prompt_tokens = getattr(usage, 'prompt_tokens', None)
        completion_tokens = getattr(usage, 'completion_tokens', None)
        total_tokens = getattr(usage, 'total_tokens', None)
        
        print(f"\n📊 Token 使用详情:")
        if prompt_tokens:
            print(f"  └─ 输入 Token (Prompt): {prompt_tokens:,}")
        if completion_tokens:
            print(f"  └─ 输出 Token (Completion): {completion_tokens:,}")
        if total_tokens:
            print(f"  └─ 总计 Token: {total_tokens:,}")
            
            # 计算Token占比
            if prompt_tokens and completion_tokens:
                prompt_pct = (prompt_tokens / total_tokens) * 100
                completion_pct = (completion_tokens / total_tokens) * 100
                print(f"  └─ 输入占比: {prompt_pct:.1f}% | 输出占比: {completion_pct:.1f}%")
    else:
        print(f"\n⚠️  无 Token 使用信息")
    
    # 响应内容
    response_chars = len(response_content)
    print(f"\n📄 响应内容:")
    print(f"  └─ 长度: {response_chars:,} 字符")
    
    if show_full_response or response_chars < 2000:
        print("-" * 100)
        print(response_content)
        print("-" * 100)
    else:
        print("-" * 100)
        print(response_content[:1000])
        print("\n... [中间内容已省略] ...\n")
        print(response_content[-500:])
        print("-" * 100)
        print(f"⚠️  提示: 响应总长度 {response_chars:,} 字符，已省略中间部分")
    
    print("="*100 + "\n")


async def web_search(query: str, max_results: int = 3) -> dict:
    """
    网络搜索工具 - 可以用于查找课程相关的背景知识
    
    Args:
        query: 搜索查询字符串
        max_results: 最大返回结果数
    
    Returns:
        dict: 搜索结果
    """
    search_url = "https://space.ai-builders.com/backend/v1/search/"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "keywords": [query],
        "max_results": max_results
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(search_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Web search 失败: {e}")
        return {"error": str(e), "queries": []}


async def fetch_url_content(url: str) -> str:
    """抓取网页内容"""
    try:
        # 设置浏览器头部，避免被反爬虫拦截
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as http_client:
            response = await http_client.get(url)
            response.raise_for_status()
            
            # 解析 HTML，提取文本内容
            soup = BeautifulSoup(response.text, 'html.parser')
            # 移除 script 和 style 标签
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # 尝试提取主要内容区域
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                # 如果没有找到主要内容区域，提取整个 body
                body = soup.find('body')
                if body:
                    text = body.get_text(separator='\n', strip=True)
                else:
                    text = soup.get_text(separator='\n', strip=True)
            
            # 清理多余的空白行
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            
            return text[:8000]  # 增加长度限制以获取更多内容
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            raise HTTPException(
                status_code=400, 
                detail=f"无法访问该 URL（403 Forbidden）。这可能是因为：1) 网站需要登录认证 2) 网站有反爬虫保护。建议：尝试复制页面内容直接粘贴，或使用公开可访问的 URL。"
            )
        raise HTTPException(status_code=400, detail=f"无法抓取 URL 内容: HTTP {e.response.status_code} - {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法抓取 URL 内容: {str(e)}")


def build_analysis_prompt(urls: List[str], texts: List[str], all_contents: List[Dict]) -> str:
    """构建 AI 分析提示词"""
    prompt = """你是一位资深的教学专家和知识架构师。请分析以下课程内容，提取逻辑骨架和知识依赖关系。

要求：
1. **识别主线逻辑**：课程的核心思想、步骤流程、关键主张（用 type: "main" 标记）
2. **识别支线知识**：达成主线目标所需的技术工具、背景概念（用 type: "dependency" 标记）
3. **跨篇章关联**：如果内容来自多个来源，标注知识点之间的继承或引用关系
4. **解释关系**：为每个依赖关系说明"为什么需要这个工具/概念"

返回严格的 JSON 格式：
{
  "nodes": [
    {
      "id": "n1",
      "label": "节点名称",
      "type": "main" | "dependency",
      "source": "url1" | "text1",  // 来源标识
      "description": "节点描述"
    }
  ],
  "edges": [
    {
      "source": "n1",
      "target": "n2",
      "type": "depends_on" | "references" | "implements",
      "reason": "为什么需要这个依赖"
    }
  ],
  "summary": "整体课程逻辑的简要总结"
}

内容：
"""
    for i, content in enumerate(all_contents):
        source_label = content['source']
        prompt += f"\n\n=== 来源 {source_label} ===\n{content['text']}\n"
    
    return prompt


# ==================== API 端点 ====================

@app.get("/")
async def read_root():
    """返回前端页面（优先返回 Next.js 静态导出）"""
    # 优先返回 Next.js 静态导出的 index.html
    next_index_path = frontend_out_dir / "index.html"
    if next_index_path.exists():
        return FileResponse(str(next_index_path), media_type="text/html")
    
    # 回退到 v1 版本的 index.html
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    
    return {"message": "LinkLog API", "status": "running", "version": VERSION}


@app.post("/api/analyze")
async def analyze_course(request: AnalyzeRequest):
    """
    分析课程内容，生成知识图谱数据
    支持多个 URL 和文本输入
    """
    print("\n" + "="*80)
    print("🚀 LinkLog - 开始分析课程")
    print("="*80)
    
    all_contents = []
    
    # ==================== 步骤 1: Agent 动作 - 处理输入 ====================
    print("\n[Agent] 步骤 1: 处理输入数据")
    print("-" * 80)
    
    # 处理 URL
    if request.urls:
        print(f"[Agent] 检测到 {len(request.urls)} 个 URL，开始抓取内容...")
        for i, url in enumerate(request.urls, 1):
            print(f"  [{i}/{len(request.urls)}] 正在抓取: {url[:60]}...")
            try:
                text = await fetch_url_content(url)
                all_contents.append({
                    "source": f"url{i}",
                    "url": url,
                    "text": text
                })
                print(f"  ✅ 成功抓取，内容长度: {len(text)} 字符")
            except Exception as e:
                print(f"  ❌ 抓取失败: {str(e)}")
                raise HTTPException(status_code=400, detail=f"处理 URL {url} 失败: {str(e)}")
    
    # 处理文本
    if request.texts:
        print(f"[Agent] 检测到 {len(request.texts)} 段文本输入")
        for i, text in enumerate(request.texts, 1):
            text_preview = text[:50] + "..." if len(text) > 50 else text
            print(f"  [{i}/{len(request.texts)}] 文本内容: {text_preview}")
            all_contents.append({
                "source": f"text{i}",
                "text": text
            })
    
    if not all_contents:
        print("[Agent] ❌ 错误: 没有可处理的内容")
        raise HTTPException(status_code=400, detail="至少需要提供一个 URL 或文本")
    
    print(f"[Agent] ✅ 输入处理完成，共 {len(all_contents)} 个内容源")
    
    # ==================== 步骤 2: System 动作 - 构建提示词 ====================
    print("\n[System] 步骤 2: 构建 AI 分析提示词")
    print("-" * 80)
    
    # 构建提示词
    prompt = build_analysis_prompt(request.urls, request.texts, all_contents)
    total_chars = sum(len(c['text']) for c in all_contents)
    print(f"[System] ✅ 提示词构建完成")
    print(f"  - 总内容长度: {total_chars:,} 字符")
    print(f"  - 提示词长度: {len(prompt):,} 字符")
    print(f"  - 内容源数量: {len(all_contents)}")
    
    # ==================== 步骤 3: System 动作 - 调用 AI ====================
    print("\n[System] 步骤 3: 调用 AI 模型进行分析")
    print("-" * 80)
    print(f"[System] 模型: deepseek")
    print(f"[System] 温度: 0.3 (低随机性，更稳定)")
    print(f"[System] 最大 Token: 2000")
    print(f"[System] 正在发送请求到 AI API...")
    
    try:
        # 调用 AI 分析（异步）
        response = await client.chat.completions.create(
            model="deepseek",  # 使用经济型模型
            messages=[
                {
                    "role": "system",
                    "content": """你是一位知识架构专家，擅长将复杂的课程内容解构为清晰的逻辑骨架和知识依赖关系。

**重要：JSON 格式要求**
1. 所有字符串中的特殊字符（引号、换行符、反斜杠等）必须正确转义
2. 字符串中的双引号必须转义为 \\"
3. 不要在 JSON 字符串中使用未转义的引号
4. 不要在对象或数组的最后一个元素后添加逗号
5. 返回纯 JSON，不要包含 markdown 代码块标记

返回格式：
{
  "nodes": [{"id": "n1", "label": "节点", "type": "main", "source": "text1", "description": "描述"}],
  "edges": [{"source": "n1", "target": "n2", "type": "depends_on", "reason": "原因"}],
  "summary": "总结"
}"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # 显示 API 使用情况
        if hasattr(response, 'usage'):
            usage = response.usage
            print(f"[System] ✅ AI 响应接收成功")
            print(f"  - 输入 Token: {usage.prompt_tokens:,}")
            print(f"  - 输出 Token: {usage.completion_tokens:,}")
            print(f"  - 总计 Token: {usage.total_tokens:,}")
        
        content = response.choices[0].message.content
        print(f"[System] 响应内容长度: {len(content):,} 字符")
        
        # ==================== 步骤 4: System 动作 - 解析响应 ====================
        print("\n[System] 步骤 4: 解析 AI 响应")
        print("-" * 80)
        
        # 尝试解析 JSON（AI 可能返回 markdown 代码块）
        original_content = content
        if "```json" in content:
            print("[System] 检测到 JSON 代码块格式，正在提取...")
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            print("[System] 检测到代码块格式，正在提取...")
            # 处理其他代码块格式
            parts = content.split("```")
            if len(parts) >= 3:
                content = parts[1].strip()
                # 如果第一部分是语言标识，跳过
                if content.startswith("json"):
                    content = content[4:].strip()
        else:
            print("[System] 响应为纯 JSON 格式")
        
        # 尝试修复常见的 JSON 格式问题
        def fix_json_string(json_str):
            """尝试修复常见的 JSON 格式问题"""
            # 移除尾随逗号（在对象或数组的最后一个元素后）
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            return json_str
        
        try:
            graph_data = json.loads(content)
            print("[System] ✅ JSON 解析成功")
        except json.JSONDecodeError as e:
            print(f"[System] ⚠️  JSON 解析失败，尝试修复...")
            print(f"[System] 错误位置: {e.msg} at line {e.lineno}, column {e.colno}")
            
            # 尝试修复 JSON
            try:
                fixed_content = fix_json_string(content)
                graph_data = json.loads(fixed_content)
                print("[System] ✅ JSON 修复成功")
            except:
                # 如果修复失败，尝试更激进的方法：使用正则表达式提取 JSON 对象
                print("[System] 尝试使用正则表达式提取 JSON...")
                import re
                # 尝试提取第一个完整的 JSON 对象
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        extracted_json = json_match.group(0)
                        # 再次尝试修复
                        extracted_json = fix_json_string(extracted_json)
                        graph_data = json.loads(extracted_json)
                        print("[System] ✅ 通过正则提取 JSON 成功")
                    except:
                        # 最后尝试：手动构建基本结构
                        print("[System] ⚠️  尝试构建基本数据结构...")
                        graph_data = {
                            "nodes": [],
                            "edges": [],
                            "summary": "JSON 解析失败，但已提取部分数据"
                        }
                        # 尝试提取节点信息（使用简单的正则）
                        node_pattern = r'"id"\s*:\s*"([^"]+)"\s*,\s*"label"\s*:\s*"([^"]+)"\s*,\s*"type"\s*:\s*"([^"]+)"'
                        nodes = re.findall(node_pattern, content)
                        for i, (node_id, label, node_type) in enumerate(nodes[:20]):  # 最多提取20个
                            graph_data["nodes"].append({
                                "id": node_id if node_id else f"n{i+1}",
                                "label": label,
                                "type": node_type if node_type in ["main", "dependency"] else "main",
                                "source": "text1",
                                "description": ""
                            })
                        print(f"[System] ⚠️  已提取 {len(graph_data['nodes'])} 个节点（部分数据可能丢失）")
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"无法解析 AI 返回的 JSON。错误: {str(e)}。请重试或检查输入内容。"
                    )
        
        # ==================== 步骤 5: System 动作 - 验证数据结构 ====================
        print("\n[System] 步骤 5: 验证和规范化数据结构")
        print("-" * 80)
        
        # 确保返回的数据结构正确
        if not isinstance(graph_data, dict):
            print("[System] ❌ 错误: 数据格式不正确（不是字典）")
            raise HTTPException(status_code=500, detail="AI 返回的数据格式不正确")
        
        # 确保有 nodes 和 edges
        if "nodes" not in graph_data:
            print("[System] ⚠️  警告: 缺少 nodes 字段，添加空数组")
            graph_data["nodes"] = []
        if "edges" not in graph_data:
            print("[System] ⚠️  警告: 缺少 edges 字段，添加空数组")
            graph_data["edges"] = []
        
        node_count = len(graph_data.get("nodes", []))
        edge_count = len(graph_data.get("edges", []))
        main_nodes = len([n for n in graph_data.get("nodes", []) if n.get("type") == "main"])
        dep_nodes = len([n for n in graph_data.get("nodes", []) if n.get("type") == "dependency"])
        
        print(f"[System] ✅ 数据结构验证完成")
        print(f"  - 总节点数: {node_count}")
        print(f"    ├─ 主线节点: {main_nodes}")
        print(f"    └─ 支线节点: {dep_nodes}")
        print(f"  - 总边数: {edge_count}")
        if "summary" in graph_data:
            summary_preview = graph_data["summary"][:100] + "..." if len(graph_data["summary"]) > 100 else graph_data["summary"]
            print(f"  - 摘要: {summary_preview}")
        
        # ==================== 步骤 6: Agent 回答 - 返回结果 ====================
        print("\n[Agent] 步骤 6: 返回分析结果")
        print("-" * 80)
        print("[Agent] ✅ 分析完成，准备返回结果")
        print("="*80 + "\n")
        
        return {
            "success": True,
            "data": graph_data,
            "sources": [c["source"] for c in all_contents]
        }
        
    except HTTPException:
        print("\n[System] ❌ HTTP 异常，终止处理")
        print("="*80 + "\n")
        raise
    except Exception as e:
        import traceback
        error_detail = str(e)
        print(f"\n[System] ❌ AI 分析异常: {error_detail}")
        print("[System] 错误堆栈:")
        print(traceback.format_exc())
        print("="*80 + "\n")
        raise HTTPException(status_code=500, detail=f"AI 分析失败: {error_detail}")


@app.post("/api/analyze-test")
async def analyze_course_test():
    """
    测试端点 - 直接返回固定的测试数据，不调用 AI
    用于测试前端跳转和渲染功能
    """
    print("\n" + "="*80)
    print("🧪 LinkLog - 测试模式（使用固定数据）")
    print("="*80)
    
    # 使用之前日志中的实际数据
    test_data = {
        "nodes": [
            {"id": "n1", "label": "AI-first 架构思维", "type": "main", "source": "text1", "description": "课程的核心思想：从传统性能/功能评估转向AI友好性评估"},
            {"id": "n2", "label": "选择 FastAPI", "type": "main", "source": "text1", "description": "选择 FastAPI 作为 AI 友好框架"},
            {"id": "n3", "label": "自动文档生成", "type": "dependency", "source": "text1", "description": "FastAPI 的自动文档生成特性"},
            {"id": "n4", "label": "严格数据契约", "type": "dependency", "source": "text1", "description": "FastAPI 的严格数据契约特性"},
            {"id": "n5", "label": "Python 类型系统", "type": "dependency", "source": "text1", "description": "利用 Python 的类型系统"},
            {"id": "n6", "label": "Cursor AI 编辑器", "type": "dependency", "source": "text1", "description": "使用 Cursor AI 编辑器进行开发"},
            {"id": "n7", "label": "创建第一个应用", "type": "main", "source": "text1", "description": "创建第一个 FastAPI 应用"},
            {"id": "n8", "label": "定义路由", "type": "main", "source": "text1", "description": "定义 API 路由"},
            {"id": "n9", "label": "数据验证", "type": "main", "source": "text1", "description": "使用 Pydantic 进行数据验证"},
            {"id": "n10", "label": "Pydantic", "type": "dependency", "source": "text1", "description": "Pydantic 数据验证库"},
            {"id": "n11", "label": "运行服务器", "type": "main", "source": "text1", "description": "使用 uvicorn 运行服务器"},
            {"id": "n12", "label": "uvicorn", "type": "dependency", "source": "text1", "description": "ASGI 服务器"},
            {"id": "n13", "label": "访问文档", "type": "main", "source": "text1", "description": "访问自动生成的 API 文档"},
            {"id": "n14", "label": "测试 API", "type": "main", "source": "text1", "description": "测试 API 端点"}
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "depends_on", "reason": "架构思维指导框架选择"},
            {"source": "n2", "target": "n3", "type": "implements", "reason": "FastAPI 提供自动文档生成"},
            {"source": "n2", "target": "n4", "type": "implements", "reason": "FastAPI 提供严格数据契约"},
            {"source": "n2", "target": "n5", "type": "depends_on", "reason": "基于 Python 类型系统"},
            {"source": "n2", "target": "n6", "type": "depends_on", "reason": "与 Cursor AI 编辑器配合"},
            {"source": "n1", "target": "n7", "type": "depends_on", "reason": "架构思维指导应用创建"},
            {"source": "n7", "target": "n8", "type": "depends_on", "reason": "应用需要定义路由"},
            {"source": "n8", "target": "n9", "type": "depends_on", "reason": "路由需要数据验证"},
            {"source": "n9", "target": "n10", "type": "depends_on", "reason": "使用 Pydantic 进行验证"},
            {"source": "n7", "target": "n11", "type": "depends_on", "reason": "应用需要服务器运行"},
            {"source": "n11", "target": "n12", "type": "depends_on", "reason": "使用 uvicorn 运行"},
            {"source": "n11", "target": "n13", "type": "depends_on", "reason": "运行后可以访问文档"},
            {"source": "n13", "target": "n14", "type": "depends_on", "reason": "文档用于测试 API"},
            {"source": "n3", "target": "n13", "type": "references", "reason": "自动文档生成功能"},
            {"source": "n4", "target": "n9", "type": "references", "reason": "数据契约支持验证"},
            {"source": "n5", "target": "n10", "type": "references", "reason": "Python 类型系统"},
            {"source": "n6", "target": "n7", "type": "references", "reason": "使用 Cursor 创建应用"}
        ],
        "summary": "课程构建了一个完整的AI优先开发框架，核心逻辑是从传统开发思维转向AI-first架构思维。主线包括：1) 选择FastAPI作为AI友好框架，因其自动文档生成和严格数据契约特性；2) 通过Python类型系统和Pydantic实现数据验证；3) 使用Cursor AI编辑器和uvicorn服务器完成开发流程。"
    }
    
    print("[Test] 返回测试数据")
    print(f"  - 节点数: {len(test_data['nodes'])}")
    print(f"  - 边数: {len(test_data['edges'])}")
    print("="*80 + "\n")
    
    return {
        "success": True,
        "data": test_data,
        "sources": ["test"]
    }


# ==================== v2 API Endpoints ====================

class V2InitRequest(BaseModel):
    """v2 初始图谱生成请求"""
    goal: str

class V2ExpandRequest(BaseModel):
    """v2 节点展开请求"""
    original_goal: str
    node_id: str
    node_label: str
    node_path: List[str]  # 从根到当前节点的路径
    node_category: str  # goal/action/prerequisite
    existing_nodes: List[Dict]  # 已有节点（用于去重）

class V2ContextRequest(BaseModel):
    """v2 节点上下文请求"""
    node_id: str
    node_label: str
    original_goal: str
    node_path: List[str]

@app.post("/api/v2/init")
async def v2_init_graph(request: V2InitRequest):
    """
    v2 版本：生成初始图谱（Level 1 节点）
    根据用户目标生成 3-5 个顶层节点
    """
    print("\n" + "="*80)
    print("🚀 LinkLog v2 - 生成初始图谱")
    print("="*80)
    
    # ========== 1. Agent 动作：接收用户输入 ==========
    print("\n[Agent] 📥 接收用户目标")
    print(f"   └─ 目标: {request.goal}")
    request_json = json.dumps({"goal": request.goal}, ensure_ascii=False, indent=2)
    print(f"   └─ 请求数据:\n{request_json}")
    
    # 构建提示词
    prompt = f"""你是一位技术导师专家，擅长将复杂的学习目标分解为清晰的依赖图谱。

用户目标：{request.goal}

请生成初始的知识图谱，包含 3-5 个顶层节点（Level 1），这些节点应该是达成目标的核心步骤或主要模块。

**节点分类：**
- goal: 最终目标或子目标
- action: 具体的行动步骤
- prerequisite: 前置知识或必须掌握的技能（这些是用户可能不知道的"未知的未知"）

**重要要求：**
1. 必须识别出至少 1-2 个 prerequisite 节点（用暖色高亮显示）
2. 节点描述要结合用户目标，解释"为什么需要这个"
3. **必须为所有节点创建边**：每个节点都应该至少有一条边连接（作为 source 或 target），确保图谱的完整性和逻辑连贯性
4. 边的创建要基于知识的逻辑关系：依赖关系、先后顺序、包含关系等，不要创建无意义的连接
5. 返回严格的 JSON 格式

**返回格式：**
{{
  "nodes": [
    {{
      "id": "n1",
      "label": "节点名称",
      "category": "goal|action|prerequisite",
      "description": "一句话描述这个节点"
    }}
  ],
  "edges": [
    {{
      "source": "n1",
      "target": "n2",
      "reason": "依赖原因"
    }}
  ]
}}"""
    
    try:
        # ========== 2. System 动作：准备 API 调用 ==========
        print("\n[System] 🔧 准备 AI API 调用")
        api_params = {
            "model": "grok-4-fast",  # 直接使用备用模型（deepseek不可用）
            "temperature": 0.3,
            "max_tokens": 1500  # 增加token以确保完整输出（之前1000太小导致截断）
        }
        print(f"   └─ 模型: {api_params['model']}")
        print(f"   └─ 温度: {api_params['temperature']}")
        print(f"   └─ 最大Token: {api_params['max_tokens']}")
        print(f"   └─ Prompt长度: {len(prompt)} 字符")
        
        # ========== 3. System 动作：调用 AI（异步）==========
        import time
        start_time = time.time()
        
        # 准备 System Prompt
        system_prompt_content = "你是一位技术导师专家，擅长识别学习路径中的前置知识和依赖关系。始终返回有效的 JSON 格式。"
        
        # 详细打印请求信息
        log_ai_request(
            endpoint_name="v2_init",
            system_prompt=system_prompt_content,
            user_prompt=prompt,
            model=api_params["model"],
            temperature=api_params["temperature"],
            max_tokens=api_params["max_tokens"]
        )
        
        # 使用带重试的 API 调用
        messages = [
            {
                "role": "system",
                "content": system_prompt_content
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = await call_ai_with_retry(
            client=client,
            model=api_params["model"],
            messages=messages,
            temperature=api_params["temperature"],
            max_tokens=api_params["max_tokens"],
            max_retries=3,
            retry_delay=2.0,
            disable_tools=True  # 禁用工具调用，避免token激增
        )
        
        elapsed_time = time.time() - start_time
        
        # ========== 4. Agent 响应：AI 返回结果 ==========
        message = response.choices[0].message
        content = message.content if message.content else ""
        usage = response.usage if hasattr(response, 'usage') else None
        
        # 详细打印响应信息
        log_ai_response(
            endpoint_name="v2_init",
            response_content=content,
            usage=usage,
            show_full_response=True
        )
        
        print(f"⏱️  请求耗时: {elapsed_time:.2f}秒")
        
        # ========== 5. System 动作：解析响应 ==========
        print("\n[System] 🔍 解析 AI 响应")
        original_content = content
        
        # 使用改进的 JSON 解析函数
        try:
            graph_data = parse_json_with_fallback(content)
            print(f"   └─ JSON 解析成功")
        except Exception as e:
            print(f"\n[System] ❌ JSON 解析完全失败: {str(e)}")
            print(f"   └─ 原始内容预览:\n{original_content[:500]}...")
            raise HTTPException(
                status_code=500,
                detail=f"无法解析 AI 返回的 JSON。错误: {str(e)}。请重试。"
            )
        
        # 验证数据结构
        if "nodes" not in graph_data:
            graph_data["nodes"] = []
        if "edges" not in graph_data:
            graph_data["edges"] = []
        
        # ========== 6. System 动作：确保节点连接（处理孤立节点）==========
        print("\n[System] 🔗 检查并修复孤立节点")
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]
        
        if len(nodes) > 0:
            # 收集所有有边的节点ID
            connected_node_ids = set()
            for edge in edges:
                connected_node_ids.add(edge.get("source"))
                connected_node_ids.add(edge.get("target"))
            
            # 找出孤立节点（没有边的节点）
            all_node_ids = {node.get("id") for node in nodes}
            isolated_node_ids = all_node_ids - connected_node_ids
            
            if isolated_node_ids:
                isolated_labels = [node.get("label", node.get("id")) for node in nodes if node.get("id") in isolated_node_ids]
                print(f"   ⚠️  发现 {len(isolated_node_ids)} 个孤立节点: {isolated_labels}")
                print(f"   └─ 提示: 这些节点没有边连接，建议在 Prompt 中明确要求 AI 为所有节点创建边")
                print(f"   └─ 注意: 不会强行连接，保持图谱的逻辑完整性")
            else:
                print(f"   ✅ 所有节点都已连接")
        
        # ========== 7. System 动作：返回结果 ==========
        print("\n[System] 📤 返回处理结果")
        print(f"   └─ 节点数量: {len(graph_data['nodes'])}")
        print(f"   └─ 边数量: {len(graph_data['edges'])}")
        print(f"   └─ 节点列表:")
        for i, node in enumerate(graph_data['nodes'], 1):
            print(f"      {i}. [{node.get('category', 'unknown')}] {node.get('label', 'N/A')}")
        
        response_data = {
            "success": True,
            "data": graph_data,
            "original_goal": request.goal
        }
        print(f"\n[System] ✅ 请求处理完成 (总耗时: {elapsed_time:.2f}秒)")
        print("="*80 + "\n")
        
        return response_data
    except Exception as e:
        print(f"\n[System] ❌ 错误: {str(e)}")
        import traceback
        print(f"   └─ 错误详情:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"生成初始图谱失败: {str(e)}")


@app.post("/api/v2/expand")
async def v2_expand_node(request: V2ExpandRequest):
    """
    v2 版本：展开节点，生成子节点（Level 2+）
    基于节点上下文生成前置知识子节点
    """
    print("\n" + "="*80)
    print("🚀 LinkLog v2 - 展开节点")
    print("="*80)
    
    # ========== 1. Agent 动作：接收展开请求 ==========
    print("\n[Agent] 📥 接收节点展开请求")
    print(f"   └─ 节点ID: {request.node_id}")
    print(f"   └─ 节点标签: {request.node_label}")
    print(f"   └─ 节点类型: {request.node_category}")
    print(f"   └─ 路径: {' → '.join(request.node_path)}")
    print(f"   └─ 原始目标: {request.original_goal}")
    print(f"   └─ 已有节点数: {len(request.existing_nodes)}")
    
    # 构建上下文
    existing_labels = [n.get('label', '') for n in request.existing_nodes]
    context_info = f"""
原始目标：{request.original_goal}
当前路径：{' → '.join(request.node_path)}
要展开的节点：{request.node_label}（类型：{request.node_category}）

已有节点（避免重复）：
{', '.join(existing_labels[:10])}
"""
    
    prompt = f"""你是一位技术导师专家。用户想要学习"{request.original_goal}"，现在需要展开节点"{request.node_label}"。

{context_info}

请生成这个节点的子节点（前置知识或具体步骤），通常 2-4 个子节点。

**重要要求：**
1. 子节点的解释必须回溯到原始目标"{request.original_goal}"，说明"在你的目标中，为什么需要学习这个"
2. 避免生成与已有节点重复的概念
3. 优先识别 prerequisite 类型的节点（用户可能不知道的知识）
4. **必须为所有子节点创建边**：每个子节点都应该至少有一条边连接到父节点"{request.node_label}"（source: "{request.node_id}"），确保图谱的完整性和逻辑连贯性
5. 边的创建要基于知识的逻辑关系：依赖关系、先后顺序、包含关系等，reason 字段要清晰说明为什么需要这个连接
6. 返回严格的 JSON 格式

**返回格式：**
{{
  "nodes": [
    {{
      "id": "nX",
      "label": "子节点名称",
      "category": "goal|action|prerequisite",
      "description": "结合原始目标解释为什么需要这个"
    }}
  ],
  "edges": [
    {{
      "source": "{request.node_id}",
      "target": "nX",
      "reason": "依赖原因"
    }}
  ]
}}"""
    
    try:
        # ========== 2. System 动作：准备 API 调用 ==========
        print("\n[System] 🔧 准备 AI API 调用")
        api_params = {
            "model": "grok-4-fast",  # 直接使用备用模型（deepseek不可用）
            "temperature": 0.3,
            "max_tokens": 1200  # 增加token以确保完整输出（之前800太小导致截断）
        }
        print(f"   └─ 模型: {api_params['model']}")
        print(f"   └─ 温度: {api_params['temperature']}")
        print(f"   └─ 最大Token: {api_params['max_tokens']}")
        print(f"   └─ Prompt长度: {len(prompt)} 字符")
        
        # ========== 3. System 动作：调用 AI（异步）==========
        import time
        start_time = time.time()
        
        # 准备 System Prompt
        system_prompt_content = "你是一位技术导师专家，擅长识别学习路径中的前置知识和依赖关系。始终返回有效的 JSON 格式，确保上下文一致性。"
        
        # 详细打印请求信息
        log_ai_request(
            endpoint_name="v2_expand",
            system_prompt=system_prompt_content,
            user_prompt=prompt,
            model=api_params["model"],
            temperature=api_params["temperature"],
            max_tokens=api_params["max_tokens"]
        )
        
        # 使用带重试的 API 调用
        messages = [
            {
                "role": "system",
                "content": system_prompt_content
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = await call_ai_with_retry(
            client=client,
            model=api_params["model"],
            messages=messages,
            temperature=api_params["temperature"],
            max_tokens=api_params["max_tokens"],
            max_retries=3,
            retry_delay=2.0,
            disable_tools=True  # 禁用工具调用，避免token激增
        )
        
        elapsed_time = time.time() - start_time
        
        # ========== 4. Agent 响应：AI 返回结果 ==========
        message = response.choices[0].message
        content = message.content if message.content else ""
        usage = response.usage if hasattr(response, 'usage') else None
        
        # 详细打印响应信息
        log_ai_response(
            endpoint_name="v2_expand",
            response_content=content,
            usage=usage,
            show_full_response=True
        )
        
        print(f"⏱️  请求耗时: {elapsed_time:.2f}秒")
        
        # ========== 5. System 动作：解析响应 ==========
        print("\n[System] 🔍 解析 AI 响应")
        original_content = content
        
        # 使用改进的 JSON 解析函数
        try:
            graph_data = parse_json_with_fallback(content)
            print(f"   └─ JSON 解析成功")
        except Exception as e:
            print(f"\n[System] ❌ JSON 解析完全失败: {str(e)}")
            print(f"   └─ 原始内容预览:\n{original_content[:500]}...")
            raise HTTPException(
                status_code=500,
                detail=f"无法解析 AI 返回的 JSON。错误: {str(e)}。请重试。"
            )
        
        # ========== 6. System 动作：节点去重 ==========
        print("\n[System] 🔄 执行节点去重")
        existing_labels_set = set(existing_labels)
        before_count = len(graph_data.get("nodes", []))
        filtered_nodes = [
            n for n in graph_data.get("nodes", [])
            if n.get("label", "") not in existing_labels_set
        ]
        graph_data["nodes"] = filtered_nodes
        print(f"   └─ 去重前: {before_count} 个节点")
        print(f"   └─ 去重后: {len(filtered_nodes)} 个节点")
        
        # ========== 7. System 动作：检查节点连接（不强行修复）==========
        print("\n[System] 🔗 检查节点连接情况")
        nodes = graph_data["nodes"]
        edges = graph_data.get("edges", [])
        
        if len(nodes) > 0:
            # 收集所有有边的节点ID（包括父节点）
            connected_node_ids = set()
            for edge in edges:
                connected_node_ids.add(edge.get("source"))
                connected_node_ids.add(edge.get("target"))
            
            # 父节点ID（要展开的节点）
            parent_node_id = request.node_id
            connected_node_ids.add(parent_node_id)  # 父节点也算已连接
            
            # 找出孤立节点（没有边的节点）
            all_node_ids = {node.get("id") for node in nodes}
            isolated_node_ids = all_node_ids - connected_node_ids
            
            if isolated_node_ids:
                isolated_labels = [node.get("label", node.get("id")) for node in nodes if node.get("id") in isolated_node_ids]
                print(f"   ⚠️  发现 {len(isolated_node_ids)} 个孤立节点: {isolated_labels}")
                print(f"   └─ 提示: 这些节点没有边连接到父节点，建议在 Prompt 中明确要求 AI 为所有子节点创建边")
                print(f"   └─ 注意: 不会强行连接，保持图谱的逻辑完整性")
            else:
                print(f"   ✅ 所有子节点都已连接到父节点")
        
        # ========== 8. System 动作：返回结果 ==========
        print("\n[System] 📤 返回处理结果")
        print(f"   └─ 新节点数量: {len(filtered_nodes)}")
        print(f"   └─ 新边数量: {len(graph_data.get('edges', []))}")
        if filtered_nodes:
            print(f"   └─ 新节点列表:")
            for i, node in enumerate(filtered_nodes, 1):
                print(f"      {i}. [{node.get('category', 'unknown')}] {node.get('label', 'N/A')}")
        
        print(f"\n[System] ✅ 请求处理完成 (总耗时: {elapsed_time:.2f}秒)")
        print("="*80 + "\n")
        
        return {
            "success": True,
            "data": graph_data
        }
    except Exception as e:
        print(f"\n[System] ❌ 错误: {str(e)}")
        import traceback
        print(f"   └─ 错误详情:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"展开节点失败: {str(e)}")


@app.post("/api/v2/context")
async def v2_get_context(request: V2ContextRequest):
    """
    v2 版本：获取节点上下文信息
    返回 Definition, Context, Action
    """
    print("\n" + "="*60)
    print("📖 LinkLog v2 - 获取节点上下文")
    print("="*60)
    
    # ========== 1. Agent 动作：接收上下文请求 ==========
    print("\n[Agent] 📥 接收节点上下文请求")
    print(f"   └─ 节点ID: {request.node_id}")
    print(f"   └─ 节点标签: {request.node_label}")
    print(f"   └─ 路径: {' → '.join(request.node_path)}")
    
    prompt = f"""用户的学习目标：{request.original_goal}
当前路径：{' → '.join(request.node_path)}
节点：{request.node_label}

请提供以下信息：
1. Definition: 一句话通俗解释这个节点是什么
2. Context: 结合用户目标"{request.original_goal}"，解释为什么需要学习这个
3. Action: 一个具体的行动建议（如：一条命令、一个步骤、一个资源链接）

返回 JSON 格式：
{{
  "definition": "...",
  "context": "...",
  "action": "..."
}}"""
    
    try:
        # ========== 2. System 动作：准备 API 调用 ==========
        print("\n[System] 🔧 准备 AI API 调用")
        api_params = {
            "model": "grok-4-fast",  # 直接使用备用模型（deepseek不可用）
            "temperature": 0.4,
            "max_tokens": 500  # 增加token以确保完整输出（之前300太小导致截断）
        }
        print(f"   └─ 模型: {api_params['model']}")
        print(f"   └─ 最大Token: {api_params['max_tokens']}")
        
        # ========== 3. System 动作：调用 AI（异步）==========
        import time
        start_time = time.time()
        
        # 准备 System Prompt
        system_prompt_content = "你是一位技术导师，用通俗易懂的语言解释技术概念。"
        
        # 详细打印请求信息
        log_ai_request(
            endpoint_name="v2_context",
            system_prompt=system_prompt_content,
            user_prompt=prompt,
            model=api_params["model"],
            temperature=api_params["temperature"],
            max_tokens=api_params["max_tokens"]
        )
        
        # 使用带重试的 API 调用
        messages = [
            {
                "role": "system",
                "content": system_prompt_content
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = await call_ai_with_retry(
            client=client,
            model=api_params["model"],
            messages=messages,
            temperature=api_params["temperature"],
            max_tokens=api_params["max_tokens"],
            max_retries=3,
            retry_delay=2.0,
            disable_tools=True  # 禁用工具调用，避免token激增
        )
        
        elapsed_time = time.time() - start_time
        
        # ========== 4. Agent 响应：AI 返回结果 ==========
        message = response.choices[0].message
        content = message.content if message.content else ""
        usage = response.usage if hasattr(response, 'usage') else None
        
        # 详细打印响应信息
        log_ai_response(
            endpoint_name="v2_context",
            response_content=content,
            usage=usage,
            show_full_response=True
        )
        
        print(f"⏱️  请求耗时: {elapsed_time:.2f}秒")
        
        # ========== 5. System 动作：解析响应 ==========
        print("\n[System] 🔍 解析 AI 响应")
        original_content = content
        
        # 使用改进的 JSON 解析函数
        try:
            context_data = parse_json_with_fallback(content)
            print(f"   └─ JSON 解析成功")
            print(f"   └─ Definition: {context_data.get('definition', 'N/A')[:50]}...")
        except Exception as e:
            print(f"\n[System] ❌ JSON 解析完全失败: {str(e)}")
            print(f"   └─ 原始内容预览:\n{original_content[:300]}...")
            raise HTTPException(
                status_code=500,
                detail=f"无法解析 AI 返回的 JSON。错误: {str(e)}。请重试。"
            )
        
        print(f"\n[System] ✅ 请求处理完成 (总耗时: {elapsed_time:.2f}秒)")
        print("="*60 + "\n")
        
        return {
            "success": True,
            "data": context_data
        }
    except Exception as e:
        print(f"\n[System] ❌ 错误: {str(e)}")
        import traceback
        print(f"   └─ 错误详情:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取上下文失败: {str(e)}")


@app.post("/api/search")
async def search_web_endpoint(query: str, max_results: int = 5):
    """
    独立的网络搜索端点 - 演示如何新增端点
    
    这个端点展示了：
    1. 如何定义新端点
    2. 如何调用工具函数
    3. 如何返回结果
    
    使用示例：
    POST /api/search?query=FastAPI&max_results=3
    """
    result = await web_search(query, max_results)
    return {
        "success": True,
        "query": query,
        "results": result
    }


@app.post("/api/add-url")
async def add_url_to_existing(request: URLInput):
    """
    为现有画布添加新的 URL
    返回新 URL 的解析结果，前端需要合并到现有图谱中
    """
    try:
        text = await fetch_url_content(request.url)
        
        print(f"\n[System] 步骤 2: 构建分析提示词")
        print("-" * 80)
        prompt = build_analysis_prompt([request.url], [], [{
            "source": "new_url",
            "url": request.url,
            "text": text
        }])
        print(f"[System] ✅ 提示词构建完成，长度: {len(prompt):,} 字符")
        
        print(f"\n[System] 步骤 3: 调用 AI 分析")
        print("-" * 80)
        print(f"[System] 模型: deepseek")
        response = await client.chat.completions.create(
            model="deepseek",
            messages=[
                {
                    "role": "system",
                    "content": "你是一位知识架构专家，分析新内容并识别与已有内容的关联。返回 JSON 格式。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        if hasattr(response, 'usage'):
            usage = response.usage
            print(f"[System] ✅ AI 响应接收成功")
            print(f"  - 输入 Token: {usage.prompt_tokens:,}")
            print(f"  - 输出 Token: {usage.completion_tokens:,}")
        
        content = response.choices[0].message.content
        
        print(f"\n[System] 步骤 4: 解析响应")
        print("-" * 80)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        try:
            graph_data = json.loads(content)
            node_count = len(graph_data.get("nodes", []))
            edge_count = len(graph_data.get("edges", []))
            print(f"[System] ✅ JSON 解析成功")
            print(f"  - 节点数: {node_count}")
            print(f"  - 边数: {edge_count}")
        except json.JSONDecodeError as e:
            print(f"[System] ❌ JSON 解析失败: {e}")
            return {
                "error": "AI 返回的 JSON 格式无效",
                "raw_content": content
            }
        
        print(f"\n[Agent] 步骤 5: 返回结果")
        print("-" * 80)
        print(f"[Agent] ✅ 新 URL 分析完成，准备合并到现有图谱")
        print("="*80 + "\n")
        
        return {
            "success": True,
            "data": graph_data,
            "url": request.url
        }
        
    except Exception as e:
        print(f"\n[System] ❌ 添加 URL 失败: {str(e)}")
        print("="*80 + "\n")
        raise HTTPException(status_code=500, detail=f"添加 URL 失败: {str(e)}")


# 处理 Next.js 静态导出的所有路由（SPA 回退）
# 必须在所有 API 路由之后定义，否则会拦截 API 请求
@app.get("/{path:path}")
async def serve_frontend(path: str):
    """服务 Next.js 前端路由（SPA 回退）"""
    # 如果是 API 路由，跳过（应该已经被上面的路由处理了）
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # 如果是静态资源（_next, public），跳过（应该已经被上面的 mount 处理了）
    if path.startswith("_next/") or path.startswith("public/"):
        raise HTTPException(status_code=404, detail="Static resource not found")
    
    # 尝试返回对应的 HTML 文件
    html_path = frontend_out_dir / path / "index.html"
    if html_path.exists():
        return FileResponse(str(html_path), media_type="text/html")
    
    # 回退到根 index.html（SPA 路由）
    index_path = frontend_out_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    
    raise HTTPException(status_code=404, detail="Page not found")


if __name__ == "__main__":
    import uvicorn
    print(f"\n{'='*80}")
    print(f"🚀 LinkLog {VERSION} 启动中...")
    print(f"{'='*80}")
    print(f"📡 服务地址: http://0.0.0.0:{PORT}")
    print(f"📚 API 文档: http://0.0.0.0:{PORT}/docs")
    print(f"📁 静态文件目录: {static_dir}")
    if frontend_out_dir.exists():
        print(f"✓ Next.js 静态导出目录存在: {frontend_out_dir}")
    else:
        print(f"⚠ Next.js 静态导出目录不存在: {frontend_out_dir}")
    if static_dir.exists():
        print(f"✓ v1 静态文件目录存在")
    else:
        print(f"⚠ v1 静态文件目录不存在")
    print(f"🔑 API Key: {api_key[:20]}...")
    print(f"{'='*80}\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")

