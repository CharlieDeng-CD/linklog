# Logic Linker (逻辑串联器)

## 项目背景
在学习文字版课程时，用户往往能理解主旨，但对其中涉及的陌生技术细节（支流知识）感到迷茫。Logic Linker 旨在通过 AI 技术解构课程逻辑，并以“画布”形式呈现主线与支线的依赖关系。

## 核心功能
- **逻辑骨架提取**：自动识别课程的层级结构和核心主张。
- **知识依赖映射**：标注达成主线目标所需的背景知识或工具（如 FastAPI, Docker 等）。
- **迷茫点高亮**：根据用户已有的知识背景，自动标记潜在的理解障碍。
- **交互式画布**：可视化主干逻辑与支流知识的连接。

## 技术栈
- **后端**: Python (FastAPI)
- **AI**: DeepSeek API (通过 OpenAI 兼容接口)
- **前端**: HTML5, JavaScript (使用 Cytoscape.js 进行画布渲染)
- **UI 设计**: 苹果风格（毛玻璃效果、圆角、优雅动画）

## 目录结构
```
logic linker/
├── server.py              # FastAPI 后端服务器
├── static/                # 前端静态文件
│   ├── index.html         # 主页面
│   ├── style.css          # 苹果风格样式
│   └── script.js          # 前端交互逻辑
├── requirements.txt       # Python 依赖
├── README.md             # 项目说明
└── product_definition.md  # 产品定义文档
```

## 快速开始

### 1. 安装依赖
```bash
cd "logic linker"
pip install -r requirements.txt
```

### 2. 配置环境变量
在项目根目录（`/Users/mugezi/Documents/projects/`）创建或更新 `.env` 文件：
```bash
AI_BUILDER_TOKEN=your_api_key_here
```

### 3. 启动服务器
```bash
python server.py
```

服务器将在 `http://localhost:8003` 启动。

### 4. 使用应用
1. 打开浏览器访问 `http://localhost:8003`
2. 在输入框中粘贴课程网页 URL
3. 点击"开始分析"，等待 AI 解析
4. 自动跳转到知识图谱画布
5. 点击节点查看详细信息
6. 使用"添加 URL"按钮继续添加更多课程页面

## 功能特性

### ✅ 已实现
- [x] 多源 URL 输入和解析
- [x] AI 自动提取逻辑主线和知识依赖
- [x] 交互式知识图谱画布（Cytoscape.js）
- [x] 节点点击查看详情
- [x] 动态添加新 URL 并合并到现有图谱
- [x] 苹果风格 UI 设计

### 🚧 待优化
- [ ] 支持文本直接输入（不限于 URL）
- [ ] 知识盲区自动高亮（基于用户背景）
- [ ] 图谱导出功能
- [ ] 更智能的跨篇章关联识别

