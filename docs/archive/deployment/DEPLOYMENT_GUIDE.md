# LinkLog 部署与版本管理指南

## 📋 目录
1. [版本管理策略](#版本管理策略)
2. [部署架构](#部署架构)
3. [版本更新流程](#版本更新流程)
4. [回滚策略](#回滚策略)
5. [最佳实践](#最佳实践)

---

## 版本管理策略

### 版本号规范
采用 [语义化版本控制 (Semantic Versioning)](https://semver.org/)：
- **主版本号 (Major)**: 不兼容的 API 变更（如 v1 → v2 → v3）
- **次版本号 (Minor)**: 向后兼容的功能新增（如 v2.0 → v2.1）
- **修订号 (Patch)**: 向后兼容的问题修复（如 v2.0.0 → v2.0.1）

### 当前版本
- **v2**: 当前开发版本（Next.js + React Flow）
- **v1**: 旧版本（HTML/CSS/JS + Cytoscape.js）

---

## 部署架构

### 推荐部署方案

#### 方案 1: 多版本并行部署（推荐）⭐

```
生产环境：
├── v2.linklog.com (当前稳定版本)
├── v3.linklog.com (新版本测试)
└── linklog.com (主域名，指向最新稳定版)
```

**优点**：
- ✅ 可以同时运行多个版本
- ✅ 新版本可以独立测试
- ✅ 支持灰度发布
- ✅ 回滚简单（切换域名指向）

**实现方式**：
- 使用 Docker 容器化部署
- 每个版本独立容器
- 通过 Nginx/负载均衡器路由

#### 方案 2: 蓝绿部署 (Blue-Green Deployment)

```
生产环境：
├── Blue (v2) - 当前生产环境
└── Green (v3) - 新版本环境
```

**流程**：
1. 在 Green 环境部署 v3
2. 测试 v3 功能
3. 切换流量：Blue → Green
4. 保留 Blue 作为回滚备份

#### 方案 3: 金丝雀发布 (Canary Release)

```
生产环境：
├── 90% 流量 → v2 (稳定版)
└── 10% 流量 → v3 (新版本)
```

**流程**：
1. 部署 v3，但只分配少量流量
2. 监控 v3 的稳定性和性能
3. 逐步增加 v3 流量比例（10% → 50% → 100%）
4. 如果出现问题，立即切回 v2

---

## 版本更新流程

### 步骤 1: 开发新版本

```bash
# 1. 创建 v3 分支
git checkout -b v3

# 2. 开发新功能
# ... 编写代码 ...

# 3. 更新版本号
# frontend/package.json
{
  "version": "3.0.0"
}

# server.py (添加版本信息)
VERSION = "3.0.0"
```

### 步骤 2: 本地测试

```bash
# 测试后端
cd linklog
python3 server.py

# 测试前端
cd frontend
npm run dev
```

### 步骤 3: 构建生产版本

```bash
# 构建前端
cd frontend
npm run build

# 构建后端 Docker 镜像（如果使用 Docker）
docker build -t linklog:v3 .
```

### 步骤 4: 部署到测试环境

```bash
# 部署到 v3.linklog.com（测试域名）
# 使用独立的服务器或容器
```

### 步骤 5: 生产环境部署

#### 如果使用方案 1（多版本并行）：

```bash
# 1. 部署 v3 到独立域名
deploy v3 → v3.linklog.com

# 2. 测试 v3 功能
# 访问 v3.linklog.com 进行完整测试

# 3. 切换主域名指向
# 在 DNS/负载均衡器中：
# linklog.com → v3.linklog.com

# 4. 保留 v2 作为备份
# v2.linklog.com 继续运行，随时可以切回
```

#### 如果使用方案 2（蓝绿部署）：

```bash
# 1. 在 Green 环境部署 v3
deploy v3 → green.linklog.com

# 2. 测试 Green 环境
# 访问 green.linklog.com

# 3. 切换流量
# 负载均衡器：Blue → Green

# 4. 监控新版本
# 观察错误日志、性能指标

# 5. 如果稳定，保留 Green；否则切回 Blue
```

---

## 回滚策略

### 快速回滚（5分钟内）

#### 方案 1: DNS/负载均衡器切换
```bash
# 立即切换域名指向
linklog.com → v2.linklog.com
```

#### 方案 2: Docker 容器切换
```bash
# 停止 v3 容器，启动 v2 容器
docker stop linklog-v3
docker start linklog-v2
```

#### 方案 3: Git 回滚 + 重新部署
```bash
# 回滚到上一个稳定版本
git checkout v2.0.0
git push origin v2.0.0 --force

# 重新部署
./deploy.sh
```

### 回滚检查清单

- [ ] 确认回滚原因（错误日志、用户反馈）
- [ ] 备份当前版本数据（数据库、用户会话）
- [ ] 通知团队回滚计划
- [ ] 执行回滚操作
- [ ] 验证回滚后功能正常
- [ ] 记录回滚原因和后续计划

---

## 最佳实践

### 1. 版本兼容性

#### API 版本控制
```python
# server.py
@app.post("/api/v2/init")  # v2 API
@app.post("/api/v3/init")  # v3 API（新版本）

# 保持 v2 API 可用，直到所有用户迁移完成
```

#### 前端版本检测
```typescript
// 检测 API 版本兼容性
const apiVersion = await fetch('/api/version');
if (apiVersion < '3.0.0') {
  // 使用兼容模式
}
```

### 2. 数据库迁移

如果 v3 需要数据库变更：

```bash
# 1. 创建迁移脚本
# migrations/v3_add_new_table.sql

# 2. 备份数据库
pg_dump linklog_db > backup_before_v3.sql

# 3. 执行迁移（在测试环境先测试）
psql linklog_db < migrations/v3_add_new_table.sql

# 4. 准备回滚脚本
# migrations/v3_rollback.sql
```

### 3. 环境变量管理

```bash
# .env.production (v2)
API_VERSION=v2
DATABASE_URL=postgresql://...

# .env.production.v3 (v3)
API_VERSION=v3
DATABASE_URL=postgresql://...  # 可以是新数据库
```

### 4. 监控和日志

```python
# server.py
import logging

# 版本信息
VERSION = "3.0.0"
logging.info(f"LinkLog v{VERSION} started")

# 请求日志包含版本信息
@app.middleware("http")
async def log_requests(request, call_next):
    response = await call_next(request)
    logging.info(f"v{VERSION} - {request.method} {request.url}")
    return response
```

### 5. 功能开关 (Feature Flags)

```python
# server.py
FEATURE_FLAGS = {
    "v3_new_feature": os.getenv("ENABLE_V3_FEATURE", "false") == "true"
}

@app.post("/api/v3/new-feature")
async def new_feature():
    if not FEATURE_FLAGS["v3_new_feature"]:
        raise HTTPException(503, "Feature not enabled")
    # ... 新功能代码 ...
```

---

## 部署检查清单

### 部署前
- [ ] 代码审查完成
- [ ] 本地测试通过
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 性能测试通过
- [ ] 安全扫描通过
- [ ] 数据库迁移脚本准备
- [ ] 回滚计划准备

### 部署中
- [ ] 备份当前版本
- [ ] 备份数据库
- [ ] 部署新版本到测试环境
- [ ] 验证测试环境功能
- [ ] 部署到生产环境
- [ ] 监控错误日志
- [ ] 监控性能指标

### 部署后
- [ ] 验证核心功能正常
- [ ] 检查错误日志
- [ ] 监控用户反馈
- [ ] 记录部署日志
- [ ] 通知团队部署完成

---

## 常见问题

### Q: 如何同时运行 v2 和 v3？

**A**: 使用不同的端口或域名：
```bash
# v2 运行在 8003
python3 server.py --port 8003

# v3 运行在 8004
python3 server.py --port 8004
```

### Q: 用户数据如何迁移？

**A**: 如果数据结构变化，需要迁移脚本：
```python
# migrations/v2_to_v3.py
def migrate_user_data():
    # 读取 v2 数据
    # 转换为 v3 格式
    # 写入 v3 数据库
```

### Q: 如何让用户知道新版本？

**A**: 在前端添加版本提示：
```typescript
// 检测新版本
if (currentVersion < latestVersion) {
  showNotification("新版本 v3 已发布！点击升级");
}
```

---

## 总结

✅ **推荐方案**：多版本并行部署（方案 1）
- 灵活性高
- 风险低
- 回滚简单

✅ **关键原则**：
1. 保持旧版本 API 可用
2. 充分测试后再切换
3. 准备回滚计划
4. 监控和日志完善

✅ **版本更新流程**：
开发 → 测试 → 部署测试环境 → 验证 → 生产部署 → 监控

---

## 相关文档

- [Git 版本管理指南](./GIT_GUIDE.md)
- [产品定义文档](./product_definition.md)
- [API 端点说明](./ENDPOINT_EXPLANATION.md)

