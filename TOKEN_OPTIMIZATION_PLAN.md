# LinkLog Token 优化方案

## 问题分析

### 当前 Token 消耗问题

1. **节点展开时的上下文膨胀**
   - 每次展开节点时，前端会传递所有 `existing_nodes`
   - 随着节点数量增加（10个 → 50个 → 100个），prompt 长度线性增长
   - 当前只取前10个节点标签，但仍有优化空间

2. **内容源全文传递**
   - `build_analysis_prompt` 会将所有内容源（网页全文）放入 prompt
   - 单个网页内容可能达到 8000 字符，多个 URL 会成倍增长

3. **重复上下文传递**
   - 每次 API 调用都会重复发送 `original_goal`、`node_path` 等固定信息
   - System prompt 每次都完整发送

## 优化方案

### 方案 1: 智能上下文压缩（推荐）⭐

#### 1.1 节点去重优化
- **问题**：前端传递所有节点，但后端只需要用于去重
- **解决**：只传递节点标签的哈希集合，而不是完整节点对象
- **效果**：从 O(n) 降低到 O(1) 的存储和比较

```python
# 优化前
existing_nodes: List[Dict]  # 每个节点包含 id, label, category 等

# 优化后
existing_labels_set: Set[str]  # 只传递标签集合
# 或者更激进：只传递标签的 MD5 哈希前8位
existing_labels_hash: Set[str]  # {"React", "FastAPI", ...}
```

#### 1.2 上下文摘要策略
- **问题**：`node_path` 可能很长（根 → 子节点1 → 子节点2 → ...）
- **解决**：只传递关键路径节点（根节点 + 当前节点的直接父节点）

```python
# 优化前
node_path: List[str]  # ["目标", "步骤1", "步骤2", "当前节点"]

# 优化后
node_path_summary: str  # "目标 → 当前节点" 或只传递关键节点
```

#### 1.3 内容源摘要
- **问题**：网页全文可能很长
- **解决**：使用 AI 先提取摘要，再用于分析

```python
async def summarize_content(text: str, max_length: int = 500) -> str:
    """使用 AI 提取内容摘要"""
    # 如果内容超过阈值，先提取摘要
    if len(text) > max_length:
        summary_prompt = f"请用100字以内总结以下内容的核心要点：\n\n{text[:2000]}"
        # 调用 AI 提取摘要
        # ...
    return text
```

### 方案 2: 缓存和会话管理

#### 2.1 会话级缓存
- **问题**：相同节点的上下文信息重复计算
- **解决**：在服务器端缓存每个会话的上下文

```python
from typing import Dict
from collections import defaultdict

# 会话缓存
session_cache: Dict[str, Dict] = defaultdict(dict)

@app.post("/api/v2/expand")
async def v2_expand_node(request: V2ExpandRequest, session_id: str):
    # 从缓存获取已有节点信息
    cached_nodes = session_cache[session_id].get('nodes', set())
    
    # 只传递新增的节点标签
    new_labels = set(request.existing_nodes) - cached_nodes
    
    # 更新缓存
    session_cache[session_id]['nodes'].update(new_labels)
```

#### 2.2 节点上下文缓存
- **问题**：相同节点的展开结果可能重复计算
- **解决**：缓存已展开节点的结果

```python
# 缓存已展开的节点
expanded_cache: Dict[str, Dict] = {}

# 如果节点已展开，直接返回缓存结果
if request.node_id in expanded_cache:
    return expanded_cache[request.node_id]
```

### 方案 3: Prompt 工程优化

#### 3.1 System Prompt 精简
- **问题**：System prompt 每次都完整发送
- **解决**：使用更简洁的 System prompt，将详细要求移到 User prompt

```python
# 优化前
system_prompt = """你是一位技术导师专家，擅长识别学习路径中的前置知识和依赖关系。始终返回有效的 JSON 格式。"""

# 优化后（更简洁）
system_prompt = "技术导师，返回 JSON。"
```

#### 3.2 结构化 Prompt
- **问题**：Prompt 中包含大量重复的格式说明
- **解决**：使用更紧凑的结构化格式

```python
# 优化前
prompt = f"""用户目标：{goal}
当前路径：{' → '.join(path)}
节点：{node_label}
已有节点：{', '.join(existing_labels[:10])}
..."""

# 优化后（使用 JSON 格式传递上下文）
prompt_context = {
    "goal": goal,
    "path": path[-2:],  # 只保留最后2个节点
    "node": node_label,
    "existing": existing_labels[:5]  # 只保留5个
}
prompt = f"展开节点：{json.dumps(prompt_context, ensure_ascii=False)}"
```

### 方案 4: 流式处理和增量更新

#### 4.1 流式响应
- **问题**：等待完整响应才能返回
- **解决**：使用流式 API，边生成边返回

```python
# 使用流式 API
stream = await client.chat.completions.create(
    model="deepseek",
    messages=[...],
    stream=True
)

# 边生成边返回
async for chunk in stream:
    # 处理 chunk
    yield chunk
```

#### 4.2 增量节点生成
- **问题**：一次生成所有子节点
- **解决**：先生成2个核心节点，用户需要时再展开

```python
# 首次展开：只生成2个核心节点
# 用户点击"展开更多"时，再生成剩余节点
```

## 实施优先级

### 第一阶段（立即实施）🔥
1. ✅ **节点标签集合优化**：只传递标签集合，不传完整节点对象
2. ✅ **路径摘要**：只传递关键路径节点（根 + 直接父节点）
3. ✅ **已有节点数量限制**：从10个减少到5个

**预期效果**：Token 消耗减少 30-50%

### 第二阶段（短期优化）📈
1. ✅ **内容摘要**：对长文本先提取摘要
2. ✅ **System Prompt 精简**：减少固定开销
3. ✅ **结构化 Prompt**：使用 JSON 格式传递上下文

**预期效果**：Token 消耗再减少 20-30%

### 第三阶段（长期优化）🚀
1. ✅ **会话缓存**：避免重复计算
2. ✅ **流式处理**：提升用户体验
3. ✅ **增量生成**：按需生成节点

**预期效果**：Token 消耗减少 50-70%

## 代码修改示例

### 修改 1: 优化 `v2_expand` 的上下文传递

```python
@app.post("/api/v2/expand")
async def v2_expand_node(request: V2ExpandRequest):
    # 优化：只提取标签，限制数量
    existing_labels = [n.get('label', '') for n in request.existing_nodes[:5]]  # 从10减少到5
    
    # 优化：路径摘要（只保留关键节点）
    path_summary = f"{request.node_path[0]} → {request.node_path[-1]}" if len(request.node_path) > 2 else " → ".join(request.node_path)
    
    # 优化：使用更紧凑的上下文格式
    context_info = f"""目标：{request.original_goal}
路径：{path_summary}
节点：{request.node_label}
已有：{', '.join(existing_labels)}"""
    
    # 优化：精简 prompt
    prompt = f"""展开节点"{request.node_label}"的子节点（2-4个）。

{context_info}

要求：
1. 回溯到目标"{request.original_goal}"
2. 避免重复：{', '.join(existing_labels)}
3. 优先识别 prerequisite 节点

返回 JSON：
{{"nodes": [{{"id": "nX", "label": "...", "category": "...", "description": "..."}}], "edges": [{{"source": "{request.node_id}", "target": "nX", "reason": "..."}}]}}"""
```

### 修改 2: 优化内容源处理

```python
async def build_analysis_prompt_optimized(urls: List[str], texts: List[str], all_contents: List[Dict]) -> str:
    """优化版：对长内容先提取摘要"""
    prompt_parts = []
    
    for content in all_contents:
        text = content['text']
        source = content['source']
        
        # 如果内容过长，先提取摘要
        if len(text) > 1000:
            summary = await summarize_content(text, max_length=500)
            prompt_parts.append(f"=== {source}（摘要）===\n{summary}")
        else:
            prompt_parts.append(f"=== {source} ===\n{text}")
    
    return "\n\n".join(prompt_parts)
```

## 监控和测量

### Token 使用监控
```python
# 添加 Token 使用统计
token_stats = {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "calls_count": 0
}

# 记录每次调用
def log_token_usage(usage):
    token_stats["prompt_tokens"] += usage.prompt_tokens
    token_stats["completion_tokens"] += usage.completion_tokens
    token_stats["total_tokens"] += usage.total_tokens
    token_stats["calls_count"] += 1
    
    # 计算平均值
    avg_prompt = token_stats["prompt_tokens"] / token_stats["calls_count"]
    print(f"平均 Prompt Token: {avg_prompt:.0f}")
```

## 预期效果

### 优化前
- 初始图谱生成：~500 tokens
- 节点展开（10个节点）：~800 tokens
- 节点展开（50个节点）：~2000 tokens
- 节点展开（100个节点）：~4000 tokens

### 优化后（第一阶段）
- 初始图谱生成：~400 tokens（-20%）
- 节点展开（10个节点）：~500 tokens（-37%）
- 节点展开（50个节点）：~800 tokens（-60%）
- 节点展开（100个节点）：~1000 tokens（-75%）

## 下一步行动

1. ✅ 实施第一阶段优化（节点标签集合、路径摘要）
2. ✅ 添加 Token 使用监控
3. ✅ 测试优化效果
4. ✅ 根据实际效果调整策略

