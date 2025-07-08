# FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04 AS builder
FROM nvidia/cuda:12.6.0-runtime-ubuntu24.04

# 防止安装过程中出现交互提示
ENV DEBIAN_FRONTEND=noninteractive
# 优先使用二进制 wheel 包加速安装
ENV PIP_PREFER_BINARY=1
# 确保 Python 输出立即显示
ENV PYTHONUNBUFFERED=1 
# 加速 CMake 构建
ENV CMAKE_BUILD_PARALLEL_LEVEL=8

# 安装 Python、git 和其他必要工具
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    wget \
    libgl1 \
    libglib2.0-0 \
    && ln -sf /usr/bin/python3.12 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# 创建并激活虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 设置工作目录
WORKDIR /app

# 复制项目文件到工作目录
COPY . /app

# 安装所有依赖
RUN pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu128 \
    && pip install -r requirements.txt \
    && python -m spacy download en_core_web_lg

RUN  chmod +x start.sh

# 暴露端口（如果项目需要）
EXPOSE 8000

# 运行项目
CMD ["./start.sh"]