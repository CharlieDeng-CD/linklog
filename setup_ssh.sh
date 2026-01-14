#!/bin/bash
# LinkLog - SSH 配置脚本

echo "🔐 配置 SSH 密钥（长期方案）"
echo "================================"
echo ""

# 步骤 1: 检查是否已有 SSH 密钥
echo "步骤 1: 检查 SSH 密钥..."
if [ -f ~/.ssh/id_ed25519.pub ]; then
    echo "✅ 找到 SSH 密钥: ~/.ssh/id_ed25519.pub"
    KEY_FILE=~/.ssh/id_ed25519.pub
elif [ -f ~/.ssh/id_rsa.pub ]; then
    echo "✅ 找到 SSH 密钥: ~/.ssh/id_rsa.pub"
    KEY_FILE=~/.ssh/id_rsa.pub
else
    echo "❌ 未找到 SSH 密钥，正在生成新的..."
    ssh-keygen -t ed25519 -C "github-key-$(date +%Y%m%d)" -f ~/.ssh/id_ed25519 -N ""
    KEY_FILE=~/.ssh/id_ed25519.pub
    echo "✅ SSH 密钥已生成！"
fi

echo ""
echo "步骤 2: 显示公钥内容"
echo "================================"
echo ""
echo "📋 请复制下面的公钥内容："
echo ""
cat "$KEY_FILE"
echo ""
echo "================================"
echo ""

# 步骤 3: 添加到 ssh-agent
echo "步骤 3: 添加到 ssh-agent..."
eval "$(ssh-agent -s)" > /dev/null 2>&1
if [ -f ~/.ssh/id_ed25519 ]; then
    ssh-add ~/.ssh/id_ed25519 2>/dev/null
elif [ -f ~/.ssh/id_rsa ]; then
    ssh-add ~/.ssh/id_rsa 2>/dev/null
fi
echo "✅ SSH agent 已配置"
echo ""

# 步骤 4: 更新 Git 远程 URL
echo "步骤 4: 更新 Git 远程 URL..."
cd "$(dirname "$0")" || exit
git remote set-url origin git@github.com:CharlieDeng-CD/linklog.git
echo "✅ Git 远程 URL 已更新为 SSH 格式"
echo ""

# 步骤 5: 测试连接
echo "步骤 5: 测试 SSH 连接..."
echo ""
echo "⚠️  请先完成以下步骤："
echo "   1. 访问 https://github.com/settings/keys"
echo "   2. 点击 'New SSH key'"
echo "   3. Title: 填写 'MacBook' 或任意名称"
echo "   4. Key: 粘贴上面显示的公钥内容"
echo "   5. 点击 'Add SSH key'"
echo ""
read -p "完成后按 Enter 继续测试连接..."
echo ""

ssh -T git@github.com 2>&1

echo ""
echo "✅ 配置完成！"
echo ""
echo "现在可以推送代码了："
echo "  git push origin main"

