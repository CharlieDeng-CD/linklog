# LinkLog Frontend (v2)

LinkLog 前端应用 - 渐进式知识图谱生成器

## 技术栈

- **Next.js 14** (App Router)
- **React 18**
- **TypeScript**
- **TailwindCSS**
- **React Flow** (知识图谱可视化)
- **Lucide React** (图标)

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:3000` 运行

### 3. 确保后端服务运行

后端 API 需要在 `http://localhost:8003` 运行：

```bash
# 在项目根目录
cd ..
python3 server.py
```

## 项目结构

```
frontend/
├── app/              # Next.js App Router
│   ├── page.tsx      # 主页面
│   ├── layout.tsx    # 根布局
│   └── globals.css   # 全局样式（包含流动渐变、毛玻璃效果）
├── components/       # React 组件
│   ├── InputScreen.tsx      # 输入界面
│   ├── GraphCanvas.tsx      # 图谱画布
│   ├── CustomNode.tsx       # 自定义节点组件（胶囊形状 + 发光）
│   └── ContextSidebar.tsx   # 上下文侧边栏
└── lib/              # 工具函数
    └── layout.ts     # 自动布局（dagre）
```

## UI 设计特性

- ✅ **流动渐变背景**：深蓝 → 紫色 → 橙色
- ✅ **毛玻璃效果**：Glassmorphism 风格
- ✅ **发光节点**：胶囊形状，Prerequisite 节点暖色高亮
- ✅ **自动布局**：使用 dagre 自动排列节点
- ✅ **背景虚化**：侧边栏打开时图谱背景虚化

## API 端点

前端调用以下后端 API：

- `POST /api/v2/init` - 生成初始图谱
- `POST /api/v2/expand` - 展开节点
- `POST /api/v2/context` - 获取节点上下文

## 开发命令

```bash
npm run dev      # 开发模式
npm run build    # 构建生产版本
npm run start    # 启动生产服务器
npm run lint     # 代码检查
```

