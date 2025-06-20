#!/bin/bash

# 格式 utf-8
export HF_HOME=huggingface
export HF_HUB_DISABLE_SYMLINKS_WARNING=1
export CUDA_PATH=

# if [ -f "./venv/bin/python" ]; then
#     PYTHON="./venv/bin/python"
#     echo "使用目录内的 python 进行启动...."
# else
#     echo "尝试使用系统 python 进行启动...."
#     PYTHON="python"
# fi

python main.py