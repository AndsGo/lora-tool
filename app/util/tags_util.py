# from wd14tagger.wd14tagger_func import get_image_tags
from prompt_gen import tag_image
from spacy_util import remove_related_tags,is_similar
from PIL import Image
from app.entity.models import ImageTags,Tags
import os
from app.config.vocab import get_vocab_list
import re
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_json_tags(completions_str):
    """
    从 LLM 完成的响应字符串中提取标签。

    :param completions_str: LLM 完成的响应字符串
    :return: 提取到的标签列表，如果未找到则返回空列表
    """ 
    json_pattern = r'"tags": "(.*?)"\n'
    json_content = re.search(json_pattern, completions_str, re.DOTALL)
    if json_content:
        return json_content.group(1).strip().split(',')
    return []

def process_image_tags(image, add_tags, remove_tags):
    """
    处理单个图片的标签，包括调用 API 生成标签、添加指定标签和移除相关标签。

    :param image: PIL 图像对象
    :param add_tags: 需要添加的标签列表
    :param remove_tags: 需要移除的相关标签列表
    :return: 处理后的标签列表
    """
    tags = []
    tags_str = tag_image(image, "tags", 1024, False, 4)
    tags = tags_str.split(",")
    add_tags.reverse()
    for tag in add_tags:
        if tag in tags:
            continue
        need_add = all(not is_similar(tag, t, 0.7) for t in tags)
        if need_add:
            tags.insert(0, tag)

    return remove_related_tags(tags, remove_tags)

def get_tags(input_folder, remove_tags: list[str], add_tags: list[str] = []):
    """
    获取指定文件夹中所有图片的标签，并进行处理。

    :param input_folder: 包含图片的文件夹路径
    :param remove_tags: 需要移除的相关标签列表
    :param add_tags: 需要添加的标签列表，默认为空列表
    :return: 包含所有图片标签信息的 Tags 对象
    """
    add_tags.reverse()
    try:
        image_files = [f for f in os.listdir(input_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
    except FileNotFoundError:
        logging.error("输入文件夹 %s 未找到", input_folder)
        return Tags(folder=input_folder, data=[])

    result = []
    for image_file in image_files:
        input_image_path = os.path.join(input_folder, image_file)
        try:
            image = Image.open(input_image_path)
            tags = process_image_tags(image, add_tags, remove_tags)
            logging.info("保存 %s 的标签: %s", image_file, tags)
            result.append(ImageTags(image_name=image_file, tags=tags))
        except Exception as e:
            logging.error("处理图片 %s 时发生错误: %s", image_file, e)

    return Tags(folder=input_folder, data=result)

def get_one_tags(input_image_path, remove_tags: list[str], add_tags: list[str] = [])->ImageTags:
    """
    获取指定文件夹中所有图片的标签，并进行处理。

    :param input_folder: 包含图片的文件夹路径
    :param remove_tags: 需要移除的相关标签列表
    :param add_tags: 需要添加的标签列表，默认为空列表
    :return: 包含所有图片标签信息的 Tags 对象
    """
    try:
        image = Image.open(input_image_path)
        tags = process_image_tags(image, add_tags, remove_tags)
        return tags
    except Exception as e:
        logging.error("处理图片 %s 时发生错误: %s", image_file, e)

def save_tags(tags:Tags):
    """
    将处理后的图片标签保存到对应的文本文件中。

    :param tags: 包含所有图片标签信息的 Tags 对象
    """
    output_folder = tags.folder
    # 遍历每个图片文件
    for image_tags in tags.data:
        # 构建输出提示词的完整路径
        output_tags_path = os.path.join(output_folder, image_tags.image_name.split(".")[0]+".txt")
        # 保存输出提示词
        with open(output_tags_path, "w") as f:
            f.write(",".join(image_tags.tags))

def translate_tags(tags_list:list[str],target_language:str="zh-CN")->dict:
    """
    翻译给定的标签列表到指定语言。

    :param tags_list: 需要翻译的标签列表
    :param target_language: 目标语言代码，默认为 "zh-CN"
    :return: 包含原始标签和翻译后标签映射的字典
    """
    from deep_translator import google
    if len(tags_list) == 0:
        return {}
    # 去重
    tags_list = list(set(tags_list)) 
    # tags_list to str
    tags_list_str = "\n".join(tags_list).replace("_"," ")
    # 翻译
    tags_list_str = google.GoogleTranslator(target=target_language).translate(tags_list_str)
    # str to list
    tags_list_translated = tags_list_str.split("\n")
    tags_map = {}
    for i in range(len(tags_list)):
        tags_map[tags_list[i]] = tags_list_translated[i]
    return tags_map

def get_noun_words(query:str):
    """
    根据查询字符串获取名词词汇列表。

    :param query: 查询字符串
    :return: 名词词汇列表
    :raises RuntimeError: 如果处理名词词汇时发生错误
    """
    try:
       return get_vocab_list(query=query)
    except Exception as e:
        raise RuntimeError(f"Error occurred while processing noun words for : {e}")