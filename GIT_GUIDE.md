# LinkLog - Git 版本管理指南

## 快速开始

### 1. 初始化仓库（如果还没有）
```bash
cd linklog
git init
```

### 2. 首次提交
```bash
# 添加所有文件
git add .

# 创建首次提交
git commit -m "Initial commit: LinkLog MVP"
```

## 基本工作流程

### 日常开发流程

```bash
# 1. 查看当前状态
git status

# 2. 查看修改内容
git diff

# 3. 添加修改的文件
git add <文件名>          # 添加单个文件
git add .                # 添加所有修改

# 4. 提交更改
git commit -m "描述你的修改"

# 5. 查看提交历史
git log --oneline
```

## 提交信息规范

建议使用清晰的提交信息：

```bash
# 功能添加
git commit -m "feat: 添加文本输入功能"

# 问题修复
git commit -m "fix: 修复屏幕切换问题"

# 样式改进
git commit -m "style: 改进苹果风格 UI"

# 文档更新
git commit -m "docs: 更新 README"
```

## 常用命令

### 查看状态和差异
```bash
git status              # 查看工作区状态
git diff                # 查看未暂存的修改
git diff --staged       # 查看已暂存的修改
git log                 # 查看提交历史
git log --oneline       # 简洁的提交历史
```

### 撤销操作
```bash
# 撤销工作区的修改（未 add）
git checkout -- <文件名>

# 撤销已暂存的修改（已 add，未 commit）
git reset HEAD <文件名>

# 修改最后一次提交
git commit --amend
```

### 分支管理（可选）
```bash
# 创建新分支
git branch <分支名>

# 切换分支
git checkout <分支名>

# 创建并切换分支
git checkout -b <分支名>

# 查看所有分支
git branch

# 合并分支
git merge <分支名>
```

## 重要文件说明

### 应该提交的文件
- ✅ `server.py` - 后端代码
- ✅ `static/` - 前端文件
- ✅ `requirements.txt` - 依赖列表
- ✅ `README.md` - 项目说明
- ✅ `.gitignore` - Git 忽略规则

### 不应该提交的文件（已在 .gitignore 中）
- ❌ `.env` - 环境变量（包含 API 密钥）
- ❌ `__pycache__/` - Python 缓存
- ❌ `*.log` - 日志文件
- ❌ `.DS_Store` - macOS 系统文件

## 当前项目状态

运行以下命令查看当前状态：
```bash
cd linklog
git status
```

## 首次完整提交示例

```bash
# 1. 检查状态
git status

# 2. 添加所有文件
git add .

# 3. 创建首次提交
git commit -m "feat: LinkLog MVP - 课程知识图谱分析工具

- 实现多源 URL 和文本输入
- AI 自动提取逻辑主线和知识依赖
- 交互式知识图谱画布（Cytoscape.js）
- 苹果风格 UI 设计
- 跨篇章知识关联
- 详细的执行过程日志"

# 4. 查看提交
git log --oneline
```

## 后续开发建议

1. **频繁提交**：每完成一个小功能就提交一次
2. **清晰的提交信息**：描述你做了什么，为什么这样做
3. **不要提交敏感信息**：确保 `.env` 文件在 `.gitignore` 中
4. **定期查看历史**：`git log` 帮助你了解项目演进

