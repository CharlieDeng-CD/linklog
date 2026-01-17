# LinkLog v3 (渐进式知识图谱生成器)

## 项目简介

LinkLog 是一个基于 AI 的渐进式知识图谱生成器，旨在帮助自学者理清知识依赖关系，识别达成目标所需的前置知识。

## 核心功能

### 双引擎架构
- **Mode A - 标准探索**：从目标出发，自动生成 3 层知识依赖图谱
- **Mode B - 差距分析**：基于用户已知知识，生成 4 层知识图谱，突出需要学习的新概念
- **Mode C - 节点详解**：点击节点查看详细信息，包括类比、行动建议等

### 动态概念集成
- 在已生成的图谱中，可以随时添加新概念
- AI 自动识别新概念与现有节点的关系
- 支持已知知识的动态补充

## 技术栈

- **后端**: Python (FastAPI)
- **前端**: Next.js (App Router), React Flow, TailwindCSS
- **AI**: OpenAI API / DeepSeek-V3 / Gemini 1.5 Pro
- **可视化**: React Flow (Dagre 布局)

## 目录结构

```
linklog/
├── server.py              # FastAPI 后端服务器
├── requirements.txt       # Python 依赖
├── frontend/              # Next.js 前端应用
│   ├── app/              # App Router 页面
│   ├── components/       # React 组件
│   ├── lib/              # 工具函数
│   └── package.json      # 前端依赖
├── scripts/              # 测试和部署脚本
├── docs/                 # 项目文档
│   ├── archive/          # 历史文档
│   └── README.md         # 文档说明
└── README.md             # 项目说明
```

## 快速开始

### 1. 安装后端依赖

```bash
cd linklog
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
AI_BUILDER_TOKEN=your_api_key_here
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 启动开发服务器

**后端**:
```bash
python server.py
```

**前端**:
```bash
cd frontend
npm run dev
```

访问 `http://localhost:3000` 查看应用。

## 生产部署

### Docker 部署

```bash
docker-compose up -d
```

### 手动部署

参考 `docs/archive/deployment/DEPLOYMENT_GUIDE.md`

## 功能特性

### ✅ v3 已实现
- [x] 双引擎架构 (Mode A/B)
- [x] 节点详解功能 (Mode C)
- [x] 动态概念集成
- [x] 中文内容支持
- [x] 交互式图谱操作（展开、详情、布局切换）
- [x] 侧边栏聊天功能
- [x] 已知知识可视化（虚线边框样式）

### 📚 文档

- [v3 产品规范](docs/archive/prd/v3/SPEC_V3.md)
- [v3 Prompt 设计](docs/archive/prd/v3/prompt.md)
- [部署指南](docs/archive/deployment/DEPLOYMENT_GUIDE.md)
- [Git 使用指南](docs/GIT_GUIDE.md)

## 版本历史

- **v3**: 双引擎架构、动态概念集成、节点详解
- **v2**: 基础知识图谱生成
- **v1**: MVP 版本

## License

MIT
