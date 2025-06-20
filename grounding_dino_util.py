from layer_style.segment_anything_func import load_groundingdino_model
from layer_style.local_groundingdino.util.inference import Model
import numpy as np
from typing import Optional
DINO_MODEL = None
DINO_MODEL_TYPE = ""


def get_model(grounding_dino_model:str = "GroundingDINO_SwinT_OGC (694MB)")->Model:
    """
    获取 GroundingDINO 模型实例。

    此函数用于获取指定类型的 GroundingDINO 模型。如果模型已加载且类型匹配，
    则直接返回已加载的模型；否则，加载指定类型的模型。

    Args:
        grounding_dino_model (str): 要加载的 GroundingDINO 模型的类型。

    Returns:
        加载的 GroundingDINO 模型实例。
    """
    # 使用全局变量 DINO_MODEL 和 DINO_MODEL_TYPE
    global DINO_MODEL,DINO_MODEL_TYPE
    # 检查模型是否已经加载且类型匹配
    if DINO_MODEL is not None and (grounding_dino_model is None or grounding_dino_model == "" or DINO_MODEL_TYPE == grounding_dino_model) :
        # 如果模型已加载且类型匹配，直接返回已加载的模型
        return DINO_MODEL
    # 若不匹配，加载指定类型的 GroundingDINO 模型
    model = load_groundingdino_model(grounding_dino_model)
    class Model2(Model):
        def __init__(self, model,  device = "cuda"):
            self.model = model
            self.device = device
    DINO_MODEL = Model2(model, device = "cuda")
    DINO_MODEL_TYPE = grounding_dino_model
    return DINO_MODEL

def get_grounding_output(image:np.ndarray,classes:list[str],grounding_dino_model:str = "GroundingDINO_SwinT_OGC (694MB)",threshold:float = 0.35):
    """
    使用 GroundingDINO 模型进行目标检测。

    该函数接收 GroundingDINO 模型类型、输入图像、目标检测提示词和阈值作为参数，
    调用 GroundingDINO 模型进行目标检测，并返回检测结果。

    Args:
        grounding_dino_model (str): 要使用的 GroundingDINO 模型类型。
        image (Image): 用于目标检测的输入图像。
        prompt (str): 目标检测的提示词，多个类别可以用逗号、竖线或点号分隔。
        threshold (float): 目标检测的阈值，用于过滤检测结果。

    Returns:
        detections: 模型返回的目标检测结果。
    """
    # 获取 GroundingDINO 模型实例
    model = get_model(grounding_dino_model)
    # 调用模型的预测方法，根据提示词中的类别进行目标检测
    # classes 参数将提示词按逗号、竖线或点号分割成多个类别
    # box_threshold 和 text_threshold 均使用传入的阈值
    # 字符串去除前后空格
    detections = model.predict_with_classes(
        image=image,
        classes=classes,
        box_threshold=threshold,
        text_threshold=threshold
    )
    # 返回检测结果
    return detections