# 部署准备检查清单

## 📋 部署要求检查

### ✅ 1. Dockerfile 存在且配置正确
- [x] Dockerfile 存在于项目根目录
- [x] 使用多阶段构建（前端构建 + Python 运行时）
- [x] CMD 使用 shell 形式：`CMD sh -c "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"`
- [x] EXPOSE 端口：`EXPOSE 8000`
- [x] 健康检查配置正确

### ✅ 2. PORT 环境变量支持
- [x] server.py 读取 PORT：`PORT = int(os.getenv("PORT", "8003"))`
- [x] Dockerfile CMD 使用 PORT：`${PORT:-8000}`
- ⚠️ **注意**：server.py 默认是 8003，Dockerfile 默认是 8000（需要统一）

### ✅ 3. 单进程/单端口
- [x] FastAPI 服务 API 和静态文件
- [x] 静态文件通过 `app.mount()` 挂载
- [x] 前端构建产物已包含在 Dockerfile 中

### ✅ 4. GitHub 仓库
- [x] 远程仓库已配置：`git@github.com:CharlieDeng-CD/linklog.git`
- [ ] 仓库是否为公开（需要确认）
- [ ] 所有更改是否已提交并推送

### ✅ 5. 环境变量和密钥
- [x] `.env` 已在 `.gitignore` 中
- [x] `AI_BUILDER_TOKEN` 会自动注入（不需要手动配置）

## 🔧 需要修复的问题

### 问题 1: PORT 默认值不一致
- **当前**：server.py 默认 PORT=8003，Dockerfile 默认 PORT=8000
- **修复**：统一为 8000（符合部署指南）

### 问题 2: 需要创建 deploy-config.json
- **需要**：创建部署配置文件，包含：
  - repo_url
  - service_name
  - branch
  - port
  - env_vars（如果需要）

## 📝 部署步骤

### 步骤 1: 修复 PORT 默认值
- [ ] 修改 server.py 中的 PORT 默认值为 8000

### 步骤 2: 创建 deploy-config.json
- [ ] 创建部署配置文件

### 步骤 3: 确认 GitHub 仓库状态
- [ ] 确认仓库为公开
- [ ] 确认所有更改已提交并推送

### 步骤 4: 部署
- [ ] 调用部署 API

## 🎯 部署所需信息

需要从用户获取：
1. **Service Name** - 服务名称（将成为子域名）
2. **Git Branch** - 要部署的分支（如 main, master）
3. **GitHub Repo URL** - 仓库 URL（已有：https://github.com/CharlieDeng-CD/linklog）

