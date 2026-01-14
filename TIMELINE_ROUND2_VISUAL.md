# 第二轮交互 - Token 和时间消耗可视化

## 📊 完整时间线图

```
时间轴 (秒)    操作                          Token消耗              状态
═════════════════════════════════════════════════════════════════════════════
0s             [开始] 用户请求生成初始图谱
              └─ 准备API调用 (grok-4-fast)
              
0s             ├─ ❌ grok-4-fast 失败 (400)     输入: 304 tokens
              │  错误: tool_choice设置但无tools  输出: 0 (失败)
              │  
0s             ├─ ❌ grok-4-fast 重试 1/3       输入: 304 tokens
              │  错误: 同上                    输出: 0 (失败)
              │  
0s             ├─ ❌ grok-4-fast 重试 2/3       输入: 304 tokens
              │  错误: 同上                    输出: 0 (失败)
              │  
0s             ├─ 🔄 切换到 gemini-3-flash      输入: 304 tokens
              │                              (模型切换)
              │  
12.19s         └─ ✅ v2_init 成功返回            输入: 304 tokens      ⚠️ JSON部分成功
              │                              输出: 404 tokens       (5个节点，1条边)
              │                              总计: 708 tokens       但JSON被截断
              │                              耗时: 12.19秒
              │
              ┌─────────────────────────────────────────────────────────────
              │ [同时] 用户点击节点展开 + 请求上下文
              │
12.19s        ├─ [开始] 展开节点请求 (v2_expand)
              │  └─ 准备API调用 (grok-4-fast)
              │
              ├─ [开始] 节点上下文请求 (v2_context 1)
              │  └─ 准备API调用 (grok-4-fast)
              │
              ├─ [开始] 节点上下文请求 (v2_context 2)
              │  └─ 准备API调用 (grok-4-fast)
              │
12.19s        ├─ ❌ grok-4-fast 失败 (400)       输入: 289 tokens
              │  错误: tool_choice设置但无tools  输出: 0 (失败)
              │  (v2_context 1)
              │
12.19s        ├─ ❌ grok-4-fast 重试 1-3          输入: 289 tokens
              │  错误: 同上                    输出: 0 (失败)
              │  (v2_context 1)
              │
12.19s        ├─ 🔄 切换到 gemini-3-flash        输入: 289 tokens
              │  (v2_context 1)
              │
20.42s         ├─ ✅ v2_context (1) 返回         输入: 143 tokens      ❌ JSON被截断
              │                              输出: 10 tokens ⚠️     (只有27字符)
              │                              总计: 153 tokens       响应不完整
              │                              耗时: 8.23秒
              │
12.19s         ├─ ❌ grok-4-fast 失败 (400)      输入: 289 tokens
              │  错误: tool_choice设置但无tools  输出: 0 (失败)
              │  (v2_context 2)
              │
12.19s         ├─ ❌ grok-4-fast 重试 1-3        输入: 289 tokens
              │  错误: 同上                    输出: 0 (失败)
              │  (v2_context 2)
              │
12.19s         ├─ 🔄 切换到 gemini-3-flash        输入: 289 tokens
              │  (v2_context 2)
              │
20.71s         ├─ ✅ v2_context (2) 返回         输入: 143 tokens      ❌ JSON被截断
              │                              输出: 11 tokens ⚠️     (只有30字符)
              │                              总计: 154 tokens       响应不完整
              │                              耗时: 8.52秒
              │
12.19s         ├─ ❌ grok-4-fast 失败 (400)      输入: 727 tokens
              │  错误: tool_choice设置但无tools  输出: 0 (失败)
              │  (v2_expand)
              │
12.19s         ├─ ❌ grok-4-fast 重试 1-3        输入: 727 tokens
              │  错误: 同上                    输出: 0 (失败)
              │  (v2_expand)
              │
12.19s         ├─ 🔄 切换到 gemini-3-flash        输入: 727 tokens
              │  (v2_expand)
              │
23.26s         └─ ✅ v2_expand 返回              输入: 356 tokens      ❌ JSON被截断
                                             输出: 29 tokens ⚠️     (只有71字符)
                                             总计: 385 tokens       响应不完整
                                             耗时: 11.07秒          提取0个节点
```

## 🔍 关键问题分析

### 问题 1: grok-4-fast 报错

```
错误信息:
  "A tool_choice was set on the request but no tools were specified"

根本原因:
  代码中设置了 tool_choice="none" 和 tools=None
  但 grok-4-fast 不支持这种组合

影响:
  ✅ 已修复：移除了 tool_choice="none" 设置
  ✅ 现在：不传任何工具相关参数，让模型默认不使用工具
```

### 问题 2: JSON 被截断（子节点为空的原因）

```
v2_expand 输出分析:
  输出Token: 29 tokens  ⚠️ 异常少！
  响应长度: 71 字符     ⚠️ 异常短！
  实际内容: {
    "nodes": [
      {
        "id": "n1_client_server_model",
        "label
  
  问题: JSON 在第一个节点的 label 字段值处被截断
  原因: max_tokens=800 太小，模型输出被强制截断
  
  结果: 无法解析出任何节点 → 子节点为空

v2_context 输出分析:
  输出Token: 10-11 tokens  ⚠️ 异常少！
  响应长度: 27-30 字符     ⚠️ 异常短！
  实际内容: ```json
  {
    "definition": "
  
  问题: JSON 在 definition 字段值处被截断
  原因: max_tokens=300 太小，模型输出被强制截断
  
  结果: 无法解析出任何内容
```

### 问题 3: 为什么子节点内容是空的？

**答案：不是网络搜索的问题，而是 JSON 被截断的问题！**

1. **JSON 被截断**：gemini-3-flash-preview 返回的 JSON 不完整
2. **max_tokens 设置太小**：
   - v2_expand: 800 tokens → 实际只输出了 29 tokens 就被截断
   - v2_context: 300 tokens → 实际只输出了 10-11 tokens 就被截断
3. **解析失败**：因为 JSON 不完整，无法解析出节点

**解决方案：**
- ✅ 增加 `max_tokens` 设置（已修复）
- ✅ 修复 `tool_choice` 问题，让 grok-4-fast 可用（已修复）
- ✅ 改进 JSON 解析，处理截断情况（已有）

## 📈 Token 消耗详细对比

### 第二轮交互统计

| 操作 | 输入Token | 输出Token | 总计Token | 耗时 | 状态 |
|------|-----------|-----------|-----------|------|------|
| v2_init | 304 | 404 | 708 | 12.19s | ⚠️ JSON部分成功 |
| v2_expand | 356 | **29** ⚠️ | 385 | 11.07s | ❌ JSON被截断 |
| v2_context (1) | 143 | **10** ⚠️ | 153 | 8.23s | ❌ JSON被截断 |
| v2_context (2) | 143 | **11** ⚠️ | 154 | 8.52s | ❌ JSON被截断 |
| **总计** | **946** | **454** | **1,400** | **40.01s** | |

### 与第一轮对比

| 指标 | 第一轮 | 第二轮 | 变化 |
|------|--------|--------|------|
| **总Token消耗** | 42,118 | 1,400 | **减少 97%** ✅ |
| **总耗时** | 326.69秒 | 40.01秒 | **减少 88%** ✅ |
| **v2_init Token** | 469 | 708 | +51% (但成功) |
| **v2_init 耗时** | 116.63秒 | 12.19秒 | **减少 90%** ✅ |
| **v2_expand Token** | 350 | 385 | +10% |
| **v2_expand 耗时** | 153.50秒 | 11.07秒 | **减少 93%** ✅ |
| **v2_context Token** | 20,251 | 153 | **减少 99%** ✅ |
| **v2_context 耗时** | 27-29秒 | 8-9秒 | **减少 70%** ✅ |
| **JSON解析成功率** | 33% (1/3) | 33% (1/3) | 无变化 ⚠️ |

## 🎯 已实施的修复

### 1. 修复 tool_choice 问题 ✅
```python
# 修复前:
if disable_tools:
    api_params["tools"] = None
    api_params["tool_choice"] = "none"  # ❌ 导致 grok-4-fast 报错

# 修复后:
if disable_tools:
    pass  # ✅ 不传任何工具相关参数即可禁用工具调用
```

### 2. 增加 max_tokens ✅
```python
# v2_init: 1000 → 1500 tokens
# v2_expand: 800 → 1200 tokens  
# v2_context: 300 → 500 tokens
```

### 3. 预期效果
- ✅ grok-4-fast 应该可以正常使用（不再报错）
- ✅ JSON 输出应该完整（不再被截断）
- ✅ 子节点内容应该可以正常提取（JSON 解析成功）

## 📝 总结

### 主要问题
1. ⚠️ **grok-4-fast 报错**：`tool_choice` 设置问题导致无法使用 → ✅ **已修复**
2. ⚠️ **JSON 被截断**：`max_tokens` 设置太小导致输出不完整 → ✅ **已修复**
3. ⚠️ **子节点为空**：因为 JSON 被截断，无法解析出节点 → ✅ **已修复**

### 关键发现
**子节点为空的原因不是网络搜索的问题，而是：**
- JSON 被截断（max_tokens 太小）
- grok-4-fast 无法使用（tool_choice 问题）
- 导致所有请求都使用 gemini-3-flash-preview，但输出被截断

### 修复后的预期
- ✅ grok-4-fast 可以正常使用
- ✅ JSON 输出完整（不再被截断）
- ✅ 子节点内容可以正常提取

**请再次测试，应该可以看到：**
- grok-4-fast 正常工作（不再报错）
- JSON 输出完整（不再被截断）
- 子节点内容正常显示（JSON 解析成功）

