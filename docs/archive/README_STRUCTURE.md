# LinkLog 项目结构

## 📁 目录结构

```
linklog/
├── server.py                 # FastAPI 后端主文件
├── requirements.txt          # Python 依赖
├── Dockerfile                # Docker 镜像配置
├── docker-compose.yml        # Docker Compose 配置
│
├── frontend/                 # Next.js 前端应用
│   ├── app/                  # Next.js App Router
│   ├── components/           # React 组件
│   ├── lib/                  # 工具函数
│   └── package.json          # Node.js 依赖
│
├── static/                   # v1 版本静态文件
│
├── scripts/                  # 脚本文件
│   ├── deploy.py             # 部署脚本
│   ├── deploy_now.py         # 快速部署脚本
│   ├── get_deployment_logs.py # 获取部署日志
│   ├── test_api.py           # API 测试
│   └── test_config.py        # 配置测试
│
├── docs/                     # 文档目录
│   ├── README.md             # 文档说明
│   └── archive/              # 开发过程记录（不提交到 Git）
│       ├── deployment/        # 部署记录
│       ├── issues/            # 问题分析
│       ├── analysis/         # Token 分析、时间线
│       └── testing/          # 测试记录
│
└── [配置文件]
    ├── deploy-config.json    # 部署配置
    ├── deploy.sh             # Shell 部署脚本
    ├── start_server.sh       # 启动服务器脚本
    └── nginx.conf.example    # Nginx 配置示例
```

## 🚀 快速开始

### 本地开发

1. **安装后端依赖**
```bash
pip install -r requirements.txt
```

2. **安装前端依赖**
```bash
cd frontend
npm install
```

3. **启动后端服务**
```bash
python server.py
# 或
./start_server.sh
```

4. **启动前端开发服务器**
```bash
cd frontend
npm run dev
```

### 部署

使用 AI Builders 平台部署：

```bash
python scripts/deploy.py
```

详细部署说明请参考 `docs/` 目录中的文档。

## 📝 文档

- `README.md` - 项目主文档
- `product_definition.md` - 产品定义
- `ENDPOINT_EXPLANATION.md` - API 端点说明
- `GIT_GUIDE.md` - Git 使用指南
- `frontend/README.md` - 前端文档

开发过程记录文档位于 `docs/archive/` 目录，不会提交到 GitHub。
