import os
import json
import sys
sys.path.append("..")
def read_config_json():
    """读取本地版本文件"""
    img_path = os.path.join(sys.path[0],"./local_config.json")
    if not os.path.exists(img_path):
        img_path = os.path.join(sys.path[0],"./config.json")

    with open(img_path, mode='r', encoding='utf-8') as j:
        return json.load(j)

config = read_config_json()

############### File Configuration ###############
IMAGE_DIR = os.getenv("IMAGE_DIR", config.get("IMAGE_DIR")) # 数据文件目录

############### AI Configuration ###############
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", config.get("AZURE_OPENAI_API_KEY"))
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT", config.get("AZURE_ENDPOINT"))
AZURE_MODEL = os.getenv("AZURE_MODEL", config.get("AZURE_MODEL"))
TAGS_PROMPT = os.getenv("TAGS_PROMPT", config.get("TAGS_PROMPT"))
