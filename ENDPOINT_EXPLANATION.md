# 端点（Endpoint）概念详解

## 什么是端点？

**端点 = 一个特定的 URL 路径 + HTTP 方法，用于处理特定类型的请求**

### 类比理解
- **端点就像餐厅的菜单项**：
  - 菜单项 = 端点
  - 点菜 = 发送 HTTP 请求
  - 上菜 = 返回响应

### 端点的组成

一个端点由两部分组成：

1. **HTTP 方法**（Method）：
   - `GET` - 获取数据（像"查看"）
   - `POST` - 提交数据（像"创建"）
   - `PUT` - 更新数据（像"修改"）
   - `DELETE` - 删除数据（像"删除"）

2. **URL 路径**（Path）：
   - 例如：`/api/analyze`
   - 例如：`/api/search`

### 完整端点示例

```
POST /api/analyze
│    │
│    └─ URL 路径（你要访问的地址）
└─ HTTP 方法（你要做什么操作）
```

## 一个端点能做什么？

一个端点可以：
1. **接收数据**（从请求中）
2. **处理数据**（调用工具函数、调用 AI、数据库操作等）
3. **返回结果**（JSON、HTML、文件等）

### 实际例子

```python
@app.post("/api/analyze")  # ← 这就是一个端点
async def analyze_course(request: AnalyzeRequest):
    # 1. 接收数据：从 request 中获取 URLs 和文本
    urls = request.urls
    texts = request.texts
    
    # 2. 处理数据：调用工具函数
    content = await fetch_url_content(urls[0])  # 调用工具
    result = await web_search("FastAPI")        # 调用工具
    
    # 3. 返回结果：返回 JSON 数据
    return {"success": True, "data": graph_data}
```

## 端点可以被新增吗？

**可以！** 你可以随时添加新的端点。

### 如何新增端点？

只需要用装饰器 `@app.get()` 或 `@app.post()` 等定义一个函数：

```python
# 新增一个 GET 端点
@app.get("/api/hello")
async def hello():
    return {"message": "Hello, World!"}

# 新增一个 POST 端点
@app.post("/api/calculate")
async def calculate(a: int, b: int):
    return {"result": a + b}
```

## 端点的类型和用途

### 1. 数据获取端点（GET）
```python
@app.get("/api/courses")
async def get_courses():
    """获取所有课程列表"""
    return {"courses": [...]}
```

### 2. 数据创建端点（POST）
```python
@app.post("/api/analyze")
async def analyze_course(request: AnalyzeRequest):
    """分析课程内容"""
    # 处理逻辑
    return {"result": "..."}
```

### 3. 数据更新端点（PUT）
```python
@app.put("/api/courses/{course_id}")
async def update_course(course_id: int, data: dict):
    """更新课程信息"""
    # 处理逻辑
    return {"success": True}
```

### 4. 数据删除端点（DELETE）
```python
@app.delete("/api/courses/{course_id}")
async def delete_course(course_id: int):
    """删除课程"""
    # 处理逻辑
    return {"success": True}
```

## 端点的实际应用场景

### 场景 1：用户操作
- 用户点击"分析"按钮 → 前端调用 `POST /api/analyze`
- 用户查看课程列表 → 前端调用 `GET /api/courses`

### 场景 2：工具调用
- 一个端点可以调用多个工具：
```python
@app.post("/api/smart-analyze")
async def smart_analyze(request: AnalyzeRequest):
    # 调用工具 1：抓取 URL
    content = await fetch_url_content(url)
    
    # 调用工具 2：搜索背景知识
    search = await web_search("FastAPI")
    
    # 调用工具 3：AI 分析
    result = await ai_analyze(content, search)
    
    return result
```

## 总结

- **端点 = URL + HTTP 方法**，是用户访问你服务的入口
- **可以新增**：随时添加新端点来扩展功能
- **能做很多事情**：
  - 接收用户输入
  - 调用工具函数
  - 处理业务逻辑
  - 返回处理结果
- **一个端点可以调用多个工具**，工具可以在多个端点间复用

