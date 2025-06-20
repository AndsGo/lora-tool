import json
import os
# 读取当前目录下的 vocab.json
def read_config_json(name:str):
    """读取本地版本文件"""
    img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),name)

    with open(img_path, mode='r', encoding='utf-8') as j:
        return json.load(j)