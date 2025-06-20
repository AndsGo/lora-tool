from layer_style.segment_anything_func import load_sam_model
from layer_style.sam_hq.predictor import SamPredictorHQ
from segment_anything import SamPredictor
import numpy as np
import cv2

SA_MODEL = None
SA_MODEL_TYPE = ""

def get_model(model_name :str = "sam_vit_h (2.56GB)"):
    """
    获取 SAM 模型实例。

    此函数用于获取指定类型的 SAM 模型。如果模型已加载且类型匹配，"
    "则直接返回已加载的模型；否则，加载指定类型的模型。

    Args:
        model_name (str): 要加载的 SAM 模型的类型。"
    """
    # 使用全局变量 SA_MODEL 和 SA_MODEL_TYPE
    global SA_MODEL,SA_MODEL_TYPE
    # 检查模型是否已经加载且类型匹配
    if SA_MODEL is not None and (model_name is None or model_name == "" or SA_MODEL_TYPE == model_name):
        # 如果模型已加载且类型匹配，直接返回已加载的模型
        return SA_MODEL
    # 若不匹配，加载指定类型的 SAM 模型
    SA_MODEL = load_sam_model(model_name)
    SA_MODEL_TYPE = model_name
    return SA_MODEL

def segment(image: np.ndarray, xyxy: np.ndarray,model_name :str = "sam_vit_h (2.56GB)") -> np.ndarray:
    """
    使用 SAM 模型对图像中指定边界框区域进行分割

    该函数接收一个 SAM 模型实例、输入图像和一组边界框，对每个边界框对应的图像区域进行分割，
    并返回每个边界框对应的掩码。

    Args:
        sam_model (Sam): 已加载的 SAM 模型实例。
        image (np.ndarray): 输入的图像，以 NumPy 数组形式表示。
        xyxy (np.ndarray): 一组边界框，每个边界框由 [x1, y1, x2, y2] 表示，其中 (x1, y1) 是左上角坐标，(x2, y2) 是右下角坐标。

    Returns:
        np.ndarray: 每个边界框对应的掩码，以 NumPy 数组形式表示。
    """
    sam_is_hq = False
    sam_predictor = None
    sam_model = get_model(model_name)
    # 检查模型是否为 SAM-HQ 模型
    if hasattr(sam_model, 'model_name') and 'hq' in sam_model.model_name:
        sam_is_hq = True
        # 创建 SamPredictorHQ 实例，用于进行分割预测
        sam_predictor = SamPredictorHQ(sam_model, sam_is_hq)
    else:
        # 创建 SamPredictor 实例，用于进行分割预测
        sam_predictor = SamPredictor(sam_model)
    # 设置输入图像
    sam_predictor.set_image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    # 初始化结果掩码列表
    result_masks = []
    # 遍历每个边界框
    for box in xyxy:
        # 使用 SamPredictorHQ 实例对当前边界框进行分割预测
        masks, scores, logits = sam_predictor.predict(
            box=box,
            # 开启多掩码输出
            multimask_output=True
        )
        # 找到得分最高的掩码的索引
        index = np.argmax(scores)
        # 将得分最高的掩码添加到结果列表中
        result_masks.append(masks[index])
    # 将结果列表转换为 NumPy 数组并返回
    return np.array(result_masks)