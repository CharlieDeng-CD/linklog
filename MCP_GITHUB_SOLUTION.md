# MCP 与 GitHub 交互问题解决方案

## 问题描述

在使用 AI Builders 的 MCP（Model Context Protocol）时，遇到以下问题：
1. **GitHub 交互问题**：无法正常与 GitHub 仓库交互
2. **文件上传问题**：文件上传到 GitHub 时出现错误

## 问题分析

### 可能的原因

1. **MCP 服务器配置问题**
   - MCP 服务器可能没有正确配置 GitHub 认证
   - Token 权限不足

2. **GitHub API 限制**
   - Rate limiting
   - 认证方式不正确

3. **文件路径问题**
   - 文件路径格式不正确
   - 相对路径 vs 绝对路径

4. **MCP 工具调用问题**
   - 工具参数格式不正确
   - 响应解析错误

## 解决方案

### 方案 1: 直接使用 GitHub API（推荐）⭐

绕过 MCP，直接使用 GitHub API 进行交互。

#### 1.1 设置 GitHub Token

```bash
# 在 .env 文件中添加
GITHUB_TOKEN=your_github_personal_access_token
```

#### 1.2 创建 GitHub 工具函数

```python
# linklog/utils/github.py
import httpx
import os
from pathlib import Path
from typing import Optional, Dict, List

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"

async def create_or_update_file(
    repo: str,
    path: str,
    content: str,
    message: str,
    branch: str = "main"
) -> Dict:
    """
    创建或更新 GitHub 文件
    
    Args:
        repo: 仓库名称，格式：owner/repo
        path: 文件路径（相对于仓库根目录）
        content: 文件内容（base64 编码）
        message: 提交信息
        branch: 分支名称
    
    Returns:
        提交结果
    """
    import base64
    
    url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 检查文件是否存在
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params={"ref": branch})
            if response.status_code == 200:
                # 文件存在，需要获取 SHA
                existing_file = response.json()
                sha = existing_file["sha"]
            else:
                sha = None
        except:
            sha = None
        
        # 编码内容
        content_bytes = content.encode('utf-8')
        content_b64 = base64.b64encode(content_bytes).decode('utf-8')
        
        # 创建或更新文件
        payload = {
            "message": message,
            "content": content_b64,
            "branch": branch
        }
        if sha:
            payload["sha"] = sha
        
        response = await client.put(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


async def create_pull_request(
    repo: str,
    title: str,
    body: str,
    head: str,
    base: str = "main"
) -> Dict:
    """
    创建 Pull Request
    
    Args:
        repo: 仓库名称
        title: PR 标题
        body: PR 描述
        head: 源分支
        base: 目标分支
    
    Returns:
        PR 信息
    """
    url = f"{GITHUB_API_BASE}/repos/{repo}/pulls"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "title": title,
        "body": body,
        "head": head,
        "base": base
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


async def get_repo_contents(
    repo: str,
    path: str = "",
    branch: str = "main"
) -> List[Dict]:
    """
    获取仓库文件列表
    
    Args:
        repo: 仓库名称
        path: 路径（空字符串表示根目录）
        branch: 分支名称
    
    Returns:
        文件列表
    """
    url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params={"ref": branch})
        response.raise_for_status()
        return response.json()
```

#### 1.3 在 server.py 中添加 GitHub API 端点

```python
# linklog/server.py

from .utils.github import create_or_update_file, create_pull_request, get_repo_contents

@app.post("/api/github/upload")
async def github_upload_file(
    repo: str,
    path: str,
    content: str,
    message: str = "Update file",
    branch: str = "main"
):
    """
    上传文件到 GitHub
    
    Args:
        repo: 仓库名称（格式：owner/repo）
        path: 文件路径
        content: 文件内容
        message: 提交信息
        branch: 分支名称
    """
    try:
        result = await create_or_update_file(
            repo=repo,
            path=path,
            content=content,
            message=message,
            branch=branch
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@app.post("/api/github/pr")
async def github_create_pr(
    repo: str,
    title: str,
    body: str,
    head: str,
    base: str = "main"
):
    """
    创建 Pull Request
    """
    try:
        result = await create_pull_request(
            repo=repo,
            title=title,
            body=body,
            head=head,
            base=base
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建 PR 失败: {str(e)}")
```

### 方案 2: 修复 MCP 配置

#### 2.1 检查 MCP 服务器配置

```json
// mcp.json
{
  "mcpServers": {
    "ai-builders-coach": {
      "command": "npx",
      "args": [
        "-y",
        "@aibuilders/mcp-coach-server"
      ],
      "env": {
        "AI_BUILDER_TOKEN": "your_token_here",
        "GITHUB_TOKEN": "your_github_token_here"  // 添加 GitHub Token
      }
    },
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

#### 2.2 使用 MCP GitHub 服务器

如果 MCP 支持 GitHub 工具，可以直接使用：

```python
# 通过 MCP 调用 GitHub 工具
# 需要查看 MCP 服务器的具体 API
```

### 方案 3: 使用 Git 命令行（备选）

如果 API 方式有问题，可以使用 Git 命令行：

```python
import subprocess
import os
from pathlib import Path

async def git_push_file(
    repo_path: Path,
    file_path: str,
    content: str,
    commit_message: str
):
    """
    使用 Git 命令行推送文件
    """
    # 写入文件
    full_path = repo_path / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding='utf-8')
    
    # Git 操作
    subprocess.run(["git", "add", file_path], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", commit_message], cwd=repo_path, check=True)
    subprocess.run(["git", "push"], cwd=repo_path, check=True)
```

## 实施步骤

### 步骤 1: 获取 GitHub Token

1. 访问 https://github.com/settings/tokens
2. 创建新的 Personal Access Token
3. 选择权限：
   - `repo`（完整仓库访问权限）
   - `workflow`（如果需要 GitHub Actions）
4. 复制 Token 并保存到 `.env` 文件

### 步骤 2: 创建工具函数

1. 创建 `linklog/utils/github.py`
2. 实现 GitHub API 调用函数
3. 添加错误处理和重试逻辑

### 步骤 3: 添加 API 端点

1. 在 `server.py` 中添加 GitHub 相关端点
2. 添加认证和权限检查
3. 添加日志记录

### 步骤 4: 测试

1. 测试文件上传功能
2. 测试 Pull Request 创建
3. 测试错误处理

## 错误处理

### 常见错误及解决方案

1. **401 Unauthorized**
   - 检查 Token 是否正确
   - 检查 Token 是否过期
   - 检查 Token 权限是否足够

2. **403 Forbidden**
   - Token 权限不足
   - 仓库不存在或无权访问

3. **404 Not Found**
   - 仓库路径不正确
   - 文件路径不正确

4. **422 Unprocessable Entity**
   - 文件内容格式错误
   - 分支不存在

## 最佳实践

1. **Token 安全**
   - 不要将 Token 提交到代码仓库
   - 使用环境变量存储 Token
   - 定期轮换 Token

2. **错误处理**
   - 添加重试逻辑
   - 记录详细错误信息
   - 提供友好的错误提示

3. **性能优化**
   - 批量操作时使用 GitHub API 的批量接口
   - 添加缓存机制
   - 异步处理长时间操作

## 监控和日志

```python
import logging

logger = logging.getLogger(__name__)

async def create_or_update_file(...):
    try:
        logger.info(f"上传文件到 GitHub: {repo}/{path}")
        result = await _upload_file(...)
        logger.info(f"上传成功: {result.get('commit', {}).get('sha')}")
        return result
    except Exception as e:
        logger.error(f"上传失败: {str(e)}", exc_info=True)
        raise
```

## 下一步行动

1. ✅ 获取 GitHub Personal Access Token
2. ✅ 创建 GitHub 工具函数
3. ✅ 添加 API 端点
4. ✅ 测试功能
5. ✅ 添加错误处理和日志

