from fileinput import filename
from pydantic import BaseModel, Field
from typing import Optional

class BaseResponse(BaseModel):
    class Config:
        arbitrary_types_allowed = True  # 添加此配置
        extra = "forbid"

    message: str = Field(..., example="success", description="响应消息")
    code: int = Field(..., example="10000", description="响应码")

class BaseListResponse(BaseResponse):
    data: list

class BaseDataResponse(BaseResponse):
    data: any = Field(..., description="响应数据")

class BaseDictResponse(BaseResponse):
    data: dict

class GroundOutRequest(BaseModel):
    """
    目标检测请求参数
    """
    classes: list[str] = Field(..., description="目标检测的提示词，多个类别可以用点号分隔。")
    model: Optional[str] = Field("GroundingDINO_SwinT_OGC (694MB)",examples=["GroundingDINO_SwinT_OGC (694MB)"], description="要使用的 GroundingDINO 模型类型。")
    threshold: Optional[float] = Field(0.35, description="目标检测的阈值，用于过滤检测结果。")
    image_folder: Optional[str] = Field(..., description="检测的图片文件夹。")


class Detections(BaseModel):
    """
    检测结果"
    """
    xyxy: Optional[list] = Field(None, description="检测框的坐标，格式为 [x1, y1, x2, y2]。")
    mask: Optional[list]= Field(None, description="检测框的掩码，格式为 [x1, y1, x2, y2]。")
    confidence: Optional[list] = Field(None, description="检测框的置信度。")
    class_id: Optional[list] = Field(None, description="检测框的类别。")
    class_name: Optional[list] = Field(None, description="检测框的类别名称。")
    tracker_id: Optional[list] = Field(None, description="检测框的跟踪器ID。")

class NormalizeRequest(BaseModel):
    """
    归一化请求参数"
    """
    input_folder: str = Field(..., description="归一化的图片文件夹。")
    output_folder: str = Field(..., description="归一化后的图片文件夹。")
    width: Optional[int] = Field(768, description="归一化后的图片宽度。")
    height: Optional[int] = Field(768, description="归一化后的图片高度。")
    broder: Optional[int] = Field(20, description="归一化后的图片边界。")
    classes: Optional[list[str]] = Field(["face","clothing", "pants","shoes", "characters"], description="目标检测的提示词，多个类别可以用点号分隔。")
    reserves: Optional[list[str]] = Field(["clothing","pants"], description="保留的类别名称列表，用于筛选检测结果。")
    remove_face: Optional[bool] = Field(True, description="是否去除头。")
    threshold: Optional[float] = Field(0.35, description="目标检测的阈值，用于过滤检测结果。")

class AutoRequest(BaseModel):
    """
    归一化请求参数"
    """
    url: str = Field(..., description="图片的URL地址")
    filename: str = Field(..., description="图片的名称")
    task_id: str = Field("task_id", description="任务ID")
    width: Optional[int] = Field(768, description="归一化后的图片宽度。")
    height: Optional[int] = Field(768, description="归一化后的图片高度。")
    broder: Optional[int] = Field(20, description="归一化后的图片边界。")
    classes: Optional[list[str]] = Field(["face","clothing", "pants","shoes", "characters"], description="目标检测的提示词，多个类别可以用点号分隔。")
    reserves: Optional[list[str]] = Field(["clothing","pants"], description="保留的类别名称列表，用于筛选检测结果。")
    remove_face: Optional[bool] = Field(True, description="是否去除头。")
    threshold: Optional[float] = Field(0.35, description="目标检测的阈值，用于过滤检测结果。")
    remove_tags: Optional[list[str]] = Field(["face"], description="去除的标签。")
    add_tags: Optional[list[str]] = Field(["white background"], description="添加的标签。")

class TagsRequest(BaseModel):
    """
    标签请求参数"
    """
    folder: str = Field(..., description="标签的图片文件夹。")
    remove_tags: Optional[list[str]] = Field(["face"], description="去除的标签。")
    add_tags: Optional[list[str]] = Field(["white background"], description="添加的标签。")
    threshold: Optional[float] = Field(0.35, description="目标检测的阈值，用于过滤检测结果。")

class ImageTags(BaseModel):
    """
    图片标签对象
    """
    image_name: str = Field(..., description="标签的图片名称。")
    tags: Optional[list[str]] = Field(["face","clothing", "pants","shoes"], description="标签。")
    translate_tags: Optional[list[str]] = Field([], description="翻译后的标签。")

class Tags(BaseModel):
    folder:str = Field(..., description="标签的图片文件夹。")
    data: Optional[list[ImageTags]] = Field(..., description="标签数据")

class TagsResponse(BaseResponse):
    data: Tags = Field(..., description="标签数据")
