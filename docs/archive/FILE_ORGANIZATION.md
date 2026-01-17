# 文件分类整理

## 📁 工程文件（核心代码和配置）

### 后端代码
- `server.py` - FastAPI 后端主文件
- `requirements.txt` - Python 依赖列表

### 前端代码
- `frontend/` - Next.js 前端应用目录
  - `app/` - Next.js App Router 页面
  - `components/` - React 组件
  - `lib/` - 工具函数
  - `package.json` - Node.js 依赖配置
  - `tsconfig.json` - TypeScript 配置
  - `next.config.mjs` - Next.js 配置
  - `tailwind.config.ts` - TailwindCSS 配置

### 静态文件
- `static/` - v1 版本的静态文件（HTML/CSS/JS）

### Docker 配置
- `Dockerfile` - 生产环境 Docker 镜像配置
- `Dockerfile.backup` - Dockerfile 备份
- `docker-compose.yml` - Docker Compose 配置（如需要）

### 部署脚本
- `deploy.py` - AI Builders 部署脚本
- `deploy_now.py` - 快速部署脚本
- `deploy-config.json` - 部署配置
- `deploy.sh` - Shell 部署脚本
- `get_deployment_logs.py` - 获取部署日志脚本

### 测试脚本
- `test_api.py` - API 测试脚本
- `test_config.py` - 配置测试脚本

### 服务器配置
- `nginx.conf.example` - Nginx 配置示例
- `start_server.sh` - 启动服务器脚本
- `setup_ssh.sh` - SSH 设置脚本

### 运行时文件（可忽略）
- `*.log` - 日志文件
- `*.pid` - 进程 ID 文件
- `frontend/out/` - Next.js 构建输出（已构建）

---

## 📝 过程记录文件（文档和记录）

### 部署相关文档
- `DEPLOYMENT_CHECKLIST.md` - 部署检查清单
- `DEPLOYMENT_DIAGNOSIS.md` - 部署问题诊断
- `DEPLOYMENT_GUIDE.md` - 部署指南
- `DEPLOYMENT_ISSUE.md` - 部署问题记录
- `DEPLOYMENT_QUICKSTART.md` - 快速部署指南
- `DEPLOYMENT_READY.md` - 部署就绪检查
- `DEPLOYMENT_STATUS.md` - 部署状态记录
- `DEPLOYMENT_SUCCESS.md` - 部署成功记录
- `DEPLOYMENT_SUMMARY.md` - 部署总结
- `DEPLOYMENT_TIMELINE.md` - 部署时间线

### 问题分析和解决方案
- `ISSUES_CONFIRMED.md` - 已确认的问题
- `ISOLATED_NODES_SOLUTION.md` - 孤立节点问题解决方案
- `FIXES_SUMMARY.md` - 修复总结
- `AI_BUILDERS_SUPPORT_REQUEST.md` - AI Builders 支持请求

### 时间线记录
- `TIMELINE_VISUALIZATION.md` - 时间线可视化
- `TIMELINE_ROUND2_VISUAL.md` - 第二轮时间线
- `TIMELINE_ROUND3_VISUAL.md` - 第三轮时间线

### Token 分析
- `TOKEN_ANALYSIS.md` - Token 使用分析
- `TOKEN_ANALYSIS_ROUND2.md` - 第二轮 Token 分析
- `TOKEN_ANALYSIS_ROUND3.md` - 第三轮 Token 分析
- `TOKEN_OPTIMIZATION_PLAN.md` - Token 优化计划

### 测试相关
- `TESTING_CHECKLIST.md` - 测试检查清单
- `TESTING_GUIDE.md` - 测试指南

### 其他文档
- `README.md` - 项目主文档
- `product_definition.md` - 产品定义
- `GIT_GUIDE.md` - Git 使用指南
- `ENDPOINT_EXPLANATION.md` - API 端点说明
- `HTTP_METHODS_EXPLANATION.md` - HTTP 方法说明
- `INTERACTION_LOGIC_ANALYSIS.md` - 交互逻辑分析
- `MCP_GITHUB_SOLUTION.md` - MCP GitHub 解决方案
- `frontend/README.md` - 前端文档

---

## 🗂️ 建议的文件组织方案

### 方案 1：创建文档目录
```
linklog/
├── docs/                    # 所有文档
│   ├── deployment/          # 部署相关
│   ├── issues/              # 问题分析
│   ├── analysis/            # Token 分析、时间线等
│   └── guides/              # 指南类文档
├── scripts/                 # 脚本文件
│   ├── deploy.py
│   ├── deploy_now.py
│   └── get_deployment_logs.py
└── [其他工程文件]
```

### 方案 2：归档历史文档
```
linklog/
├── docs/                    # 当前有用的文档
│   ├── README.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── ...
├── archive/                 # 历史记录文档
│   ├── deployment/           # 部署过程记录
│   ├── issues/               # 问题记录
│   └── analysis/             # 分析记录
└── [其他工程文件]
```

### 方案 3：保留核心文档，归档其他
```
linklog/
├── docs/                    # 核心文档
│   ├── README.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── API.md (合并端点说明)
├── archive/                 # 归档所有过程记录
└── [其他工程文件]
```

