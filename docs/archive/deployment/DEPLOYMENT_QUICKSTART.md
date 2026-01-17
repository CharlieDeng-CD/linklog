# LinkLog v2 快速部署指南

## 🚀 快速开始

### 方式 1: 使用 Docker Compose（推荐）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 AI_BUILDER_TOKEN

# 2. 启动服务
docker-compose up -d linklog-v2

# 3. 查看日志
docker-compose logs -f linklog-v2

# 4. 访问服务
# http://localhost:8003
# http://localhost:8003/docs
```

### 方式 2: 使用部署脚本

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 2. 运行部署脚本
./deploy.sh production v2

# 3. 查看状态
docker ps | grep linklog
```

### 方式 3: 直接运行（开发环境）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
export AI_BUILDER_TOKEN=your_token_here

# 3. 启动服务
python3 server.py
```

---

## 📋 部署前检查清单

- [ ] Docker 和 Docker Compose 已安装
- [ ] `.env` 文件已配置（包含 `AI_BUILDER_TOKEN`）
- [ ] 端口 8003 未被占用
- [ ] 防火墙规则已配置（如需要）

---

## 🔧 常用命令

### Docker Compose

```bash
# 启动服务
docker-compose up -d linklog-v2

# 停止服务
docker-compose stop linklog-v2

# 重启服务
docker-compose restart linklog-v2

# 查看日志
docker-compose logs -f linklog-v2

# 查看状态
docker-compose ps

# 停止并删除容器
docker-compose down linklog-v2

# 重新构建并启动
docker-compose up -d --build linklog-v2
```

### Docker

```bash
# 构建镜像
docker build -t linklog:v2 .

# 运行容器
docker run -d \
  --name linklog-v2 \
  -p 8003:8003 \
  -e AI_BUILDER_TOKEN=your_token \
  linklog:v2

# 查看日志
docker logs -f linklog-v2

# 进入容器
docker exec -it linklog-v2 bash

# 停止容器
docker stop linklog-v2

# 删除容器
docker rm linklog-v2
```

---

## 🌐 生产环境部署

### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 部署应用

```bash
# 克隆或上传代码到服务器
git clone <your-repo-url>
cd linklog

# 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 部署
./deploy.sh production v2
```

### 3. 配置 Nginx（可选）

```bash
# 安装 Nginx
sudo apt install nginx

# 复制配置
sudo cp nginx.conf.example /etc/nginx/sites-available/linklog
sudo ln -s /etc/nginx/sites-available/linklog /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 4. 配置 SSL（可选）

```bash
# 使用 Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d linklog.com -d www.linklog.com
```

---

## 🔄 版本更新流程

### 更新到新版本（例如 v3）

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 更新 docker-compose.yml（取消注释 v3 服务）

# 3. 部署 v3 到测试端口
docker-compose up -d linklog-v3

# 4. 测试 v3
curl http://localhost:8004/docs

# 5. 如果测试通过，切换主端口
# 修改 docker-compose.yml 端口映射
# 8003 -> v3, 8004 -> v2 (备份)

# 6. 重启服务
docker-compose restart
```

---

## 🐛 故障排查

### 服务无法启动

```bash
# 查看日志
docker-compose logs linklog-v2

# 检查容器状态
docker ps -a | grep linklog

# 检查端口占用
netstat -tulpn | grep 8003
```

### API 调用失败

```bash
# 检查环境变量
docker exec linklog-v2 env | grep AI_BUILDER_TOKEN

# 测试 API
curl http://localhost:8003/docs

# 查看应用日志
docker-compose logs -f linklog-v2
```

### 容器健康检查失败

```bash
# 手动健康检查
docker exec linklog-v2 python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/docs')"

# 重启容器
docker-compose restart linklog-v2
```

---

## 📊 监控和维护

### 查看资源使用

```bash
# 容器资源使用
docker stats linklog-v2

# 磁盘使用
docker system df
```

### 备份和恢复

```bash
# 备份镜像
docker save linklog:v2 > linklog-v2-backup.tar

# 恢复镜像
docker load < linklog-v2-backup.tar

# 备份配置
tar -czf config-backup.tar.gz .env docker-compose.yml
```

---

## 🔐 安全建议

1. **环境变量安全**
   - 不要将 `.env` 文件提交到 Git
   - 使用密钥管理服务（如 AWS Secrets Manager）

2. **网络安全**
   - 配置防火墙规则
   - 使用 HTTPS（配置 SSL 证书）
   - 限制 API 访问来源

3. **容器安全**
   - 定期更新基础镜像
   - 使用非 root 用户运行容器
   - 扫描镜像漏洞：`docker scan linklog:v2`

---

## 📞 获取帮助

- 查看详细文档：`DEPLOYMENT_GUIDE.md`
- 查看 API 文档：`http://localhost:8003/docs`
- 查看日志：`docker-compose logs -f linklog-v2`

---

## ✅ 部署验证

部署完成后，验证以下内容：

- [ ] 服务可以访问：`http://localhost:8003`
- [ ] API 文档可以访问：`http://localhost:8003/docs`
- [ ] 健康检查通过：`curl http://localhost:8003/docs`
- [ ] 日志正常输出
- [ ] 容器状态为 "Up"

---

**部署成功！🎉**

