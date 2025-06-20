@REM 格式 utf-8
@echo off

set HF_HOME=huggingface
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set CUDA_PATH=

if exist ".\python\python.exe" (
    set PYTHON=python\python.exe
    echo 使用目录内的 python 进行启动....
) else (
    set PYTHON=python
    echo 尝试使用系统 python 进行启动....
)
%PYTHON% -u main.py
