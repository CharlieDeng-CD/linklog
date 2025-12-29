"""
Logic Linker - 后端服务器
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
from openai import OpenAI
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

app = FastAPI(title="Logic Linker API")

# 启用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 OpenAI 客户端
# 优先从环境变量读取，如果没有则使用默认密钥（仅用于开发）
api_key = os.getenv("AI_BUILDER_TOKEN") or "sk_a5bebbc1_a57c871039be5845359613b5c8d9856cce87"

client = OpenAI(
    base_url="https://space.ai-builders.com/backend/v1",
    api_key=api_key
)

print(f"✓ OpenAI 客户端已初始化")
print(f"  Base URL: https://space.ai-builders.com/backend/v1")
print(f"  API Key: {api_key[:20]}...")

# 静态文件目录
static_dir = Path(__file__).parent / "static"

# 挂载静态文件（必须在路由之前）
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    print(f"✓ 静态文件目录已挂载: {static_dir}")
else:
    print(f"⚠ 警告: 静态文件目录不存在: {static_dir}")

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
    """返回前端页面"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return {"message": "Logic Linker API", "status": "running", "static_dir": str(static_dir)}


@app.post("/api/analyze")
async def analyze_course(request: AnalyzeRequest):
    """
    分析课程内容，生成知识图谱数据
    支持多个 URL 和文本输入
    """
    print("\n" + "="*80)
    print("🚀 Logic Linker - 开始分析课程")
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
        # 调用 AI 分析
        response = client.chat.completions.create(
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
    print("🧪 Logic Linker - 测试模式（使用固定数据）")
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
        response = client.chat.completions.create(
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


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("🚀 Logic Linker 服务器启动中...")
    print(f"📁 静态文件目录: {static_dir}")
    print(f"🌐 访问地址: http://localhost:8003")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")

