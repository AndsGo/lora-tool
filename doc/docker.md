# Docker 部署文档

## 概述
本文档介绍如何使用 Docker 部署 LoRA 工具。

## 前提条件
- 已安装 Docker
- 了解基本的 Docker 命令

## 步骤

### 1. 拉取镜像
从 Docker Hub 拉取 LoRA 工具的镜像：
```
docker pull songandco/lora-tool:latest
```
### 2. 运行容器
使用以下命令运行容器：
```
docker run -d -p 8080:8080 songandco/lora-tool:latest
```
### 3. 访问服务
在浏览器中访问 `http://localhost:8080` 即可使用 LoRA 工具。
