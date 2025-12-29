# HTTP 方法详解

## HTTP 方法是什么？

HTTP 方法（也叫 HTTP 动词）告诉服务器"你想做什么操作"。

就像你进餐厅时：
- **GET** = "我想看看菜单"（查看）
- **POST** = "我要点菜"（创建/提交）
- **PUT** = "我要修改我的订单"（更新）
- **DELETE** = "我要取消这个菜"（删除）

## 主要 HTTP 方法

### 1. GET - 获取数据（查看）

**用途**：从服务器获取数据，不会改变服务器状态

**特点**：
- ✅ 安全（不会修改数据）
- ✅ 可以缓存
- ✅ 数据在 URL 中（查询参数）
- ❌ 不能发送大量数据

**示例**：
```python
@app.get("/api/courses")
async def get_courses():
    """获取所有课程列表"""
    return {"courses": [...]}
```

**使用场景**：
- 查看课程列表
- 获取用户信息
- 查看搜索结果
- 访问网页

**实际调用**：
```
GET http://localhost:8003/api/courses
```

---

### 2. POST - 提交数据（创建/处理）

**用途**：向服务器提交数据，通常用于创建新资源或处理复杂操作

**特点**：
- ✅ 可以发送大量数据（在请求体中）
- ✅ 数据更安全（不在 URL 中）
- ✅ 可以处理复杂操作
- ❌ 不能缓存
- ❌ 可能改变服务器状态

**示例**：
```python
@app.post("/api/analyze")
async def analyze_course(request: AnalyzeRequest):
    """分析课程内容"""
    # 处理数据
    return {"success": True, "data": result}
```

**使用场景**：
- 提交表单
- 创建新资源
- 处理复杂操作（如 AI 分析）
- 上传文件

**实际调用**：
```javascript
POST http://localhost:8003/api/analyze
Body: {
  "urls": ["https://..."],
  "texts": []
}
```

---

### 3. PUT - 更新数据（完整替换）

**用途**：更新整个资源（完整替换）

**特点**：
- ✅ 幂等性（多次调用结果相同）
- ✅ 更新整个资源
- ❌ 需要提供完整数据

**示例**：
```python
@app.put("/api/courses/{course_id}")
async def update_course(course_id: int, course_data: CourseData):
    """更新整个课程信息"""
    # 替换整个课程数据
    return {"success": True}
```

**使用场景**：
- 更新用户完整信息
- 替换整个文档
- 完整更新配置

---

### 4. PATCH - 部分更新

**用途**：只更新资源的某些字段（部分更新）

**特点**：
- ✅ 只更新指定字段
- ✅ 更灵活
- ❌ 不是幂等的

**示例**：
```python
@app.patch("/api/courses/{course_id}")
async def update_course_partial(course_id: int, updates: dict):
    """只更新课程的某些字段"""
    # 只更新提供的字段
    return {"success": True}
```

**使用场景**：
- 只修改用户名
- 只更新课程标题
- 部分更新配置

---

### 5. DELETE - 删除数据

**用途**：删除服务器上的资源

**特点**：
- ✅ 幂等性
- ✅ 简单直接
- ❌ 不可逆操作

**示例**：
```python
@app.delete("/api/courses/{course_id}")
async def delete_course(course_id: int):
    """删除课程"""
    # 删除操作
    return {"success": True}
```

**使用场景**：
- 删除课程
- 删除用户
- 删除文件

---

## 方法对比表

| 方法 | 用途 | 是否改变数据 | 数据位置 | 幂等性 | 缓存 |
|------|------|------------|---------|--------|------|
| **GET** | 获取/查看 | ❌ 否 | URL 参数 | ✅ 是 | ✅ 可缓存 |
| **POST** | 创建/处理 | ✅ 是 | 请求体 | ❌ 否 | ❌ 不可缓存 |
| **PUT** | 完整更新 | ✅ 是 | 请求体 | ✅ 是 | ❌ 不可缓存 |
| **PATCH** | 部分更新 | ✅ 是 | 请求体 | ❌ 否 | ❌ 不可缓存 |
| **DELETE** | 删除 | ✅ 是 | URL 参数 | ✅ 是 | ❌ 不可缓存 |

## 实际应用示例

### 场景：课程管理系统

```python
# 1. GET - 查看所有课程
@app.get("/api/courses")
async def list_courses():
    return {"courses": [...]}

# 2. GET - 查看单个课程
@app.get("/api/courses/{course_id}")
async def get_course(course_id: int):
    return {"course": {...}}

# 3. POST - 创建新课程
@app.post("/api/courses")
async def create_course(course_data: CourseData):
    return {"success": True, "course_id": 123}

# 4. PUT - 完整更新课程
@app.put("/api/courses/{course_id}")
async def update_course(course_id: int, course_data: CourseData):
    return {"success": True}

# 5. PATCH - 部分更新课程（只改标题）
@app.patch("/api/courses/{course_id}")
async def update_course_title(course_id: int, title: str):
    return {"success": True}

# 6. DELETE - 删除课程
@app.delete("/api/courses/{course_id}")
async def delete_course(course_id: int):
    return {"success": True}
```

## RESTful API 设计原则

RESTful API 使用 HTTP 方法来表示操作：

```
GET    /api/courses        → 获取所有课程
GET    /api/courses/1      → 获取课程 1
POST   /api/courses        → 创建新课程
PUT    /api/courses/1      → 完整更新课程 1
PATCH  /api/courses/1     → 部分更新课程 1
DELETE /api/courses/1     → 删除课程 1
```

## 在你的 Logic Linker 项目中的使用

### 当前使用的 HTTP 方法：

1. **GET `/`** - 获取前端页面
   ```python
   @app.get("/")
   async def read_root():
       return FileResponse("index.html")
   ```

2. **POST `/api/analyze`** - 分析课程（处理复杂操作）
   ```python
   @app.post("/api/analyze")
   async def analyze_course(request: AnalyzeRequest):
       # 处理分析逻辑
   ```

3. **POST `/api/search`** - 搜索（处理查询）
   ```python
   @app.post("/api/search")
   async def search_web_endpoint(query: str):
       # 执行搜索
   ```

## 选择合适的方法

### 什么时候用 GET？
- ✅ 只是查看数据
- ✅ 不需要修改服务器
- ✅ 数据可以缓存

### 什么时候用 POST？
- ✅ 创建新资源
- ✅ 处理复杂操作（如 AI 分析）
- ✅ 需要发送大量数据
- ✅ 操作不可重复

### 什么时候用 PUT？
- ✅ 完整替换资源
- ✅ 需要幂等性（多次调用结果相同）

### 什么时候用 PATCH？
- ✅ 只更新部分字段
- ✅ 不想发送完整数据

### 什么时候用 DELETE？
- ✅ 删除资源
- ✅ 不可逆操作

## 总结

- **GET** = 查看（不改变数据）
- **POST** = 创建/处理（改变数据，发送大量数据）
- **PUT** = 完整更新（替换整个资源）
- **PATCH** = 部分更新（只更新某些字段）
- **DELETE** = 删除（移除资源）

选择方法的原则：
- 只是查看？→ **GET**
- 创建或处理？→ **POST**
- 完整更新？→ **PUT**
- 部分更新？→ **PATCH**
- 删除？→ **DELETE**

