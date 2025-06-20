import segment_anything_util as sam_util
import grounding_dino_util as dino_util
import imagefunc as image_util
import torch
from PIL import Image
import cv2
import numpy as np
import os
import mimetypes
import requests
from io import BytesIO
from folder_paths import output_directory


# 定义一个处理图像的函数
# 参数 folder_path: 包含待处理图像的文件夹路径
# 参数 output_folder_path: 处理后图像的输出文件夹路径
# 参数 classes: 要检测的类别列表，默认为 ["face", "clothing", "pants", "shoes", "characters"]
# 参数 reserves: 要保留的类别列表，默认为 ["clothing", "pants"]
# 参数 remove_face: 是否移除人脸，默认为 True
# 参数 threshold: 检测阈值，默认为 0.35
# 参数 width: 输出图像的宽度，默认为 768
# 参数 height: 输出图像的高度，默认为 768
# 返回值: 一个字典列表，每个字典包含处理后的图像信息
def process_images(folder_path,
                   output_folder_path,
                   classes:list[str]=["face","clothing", "pants","shoes", "characters"],
                   reserves:list[str] = ["clothing","pants"],
                   remove_face:bool = True,
                   threshold:float = 0.3,
                   width:int = 768,
                   height:int = 768,) -> dict:
    if remove_face :
        if "face" not in classes:
            classes.append("face")
    # 创建输出文件夹（如果不存在）
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)
    # 读取文件夹中的所有图片文件，只获取第一层
    original_folder_path= os.path.join(folder_path, "original")
    if not os.path.exists(original_folder_path):
        os.makedirs(original_folder_path)
    # 读取文件夹中的所有图片文件，只获取第一层
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    # 遍历每个图片文件
    result = []
    for image_file in image_files:
        # 构建输入图片的完整路径
        input_image_path = os.path.join(folder_path, image_file)    
        # 构建输出图片的完整路径
        output_image_path = os.path.join(output_folder_path, image_file)
        # 读取输入图片
        image = Image.open(input_image_path)
        # 根据图片的EXIF信息，并旋转图片
        image = rotate_image_by_exif(image)
        image = image_util.pil2cv2(image)
        detections = dino_util.get_grounding_output(image=image, classes=classes,threshold=threshold)
        detections.mask = sam_util.segment(image, detections.xyxy)

        total_mask = detections.mask[0].copy()
        for _, mask in enumerate(detections.mask):
            # 将掩码转换为布尔类型
            mask_bool = mask.astype(bool)
            # 将掩码应用于原始图像
            total_mask[mask_bool] = 255
        _image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGBA))
        xyxy = image_util.get_max_xyxy(detections=detections,CLASSES=classes
                                ,reserves=reserves,_image=_image,broder=10)
        # xyxy[0] = xyxy[0]-0.1*min(xyxy[2]-xyxy[0],xyxy[3]-xyxy[1])
        # xyxy[1] = xyxy[1]-0.1*min(xyxy[2]-xyxy[0],xyxy[3]-xyxy[1])
        # 多漏点脚
        xyxy[2] = xyxy[2]+0.1*(xyxy[2]-xyxy[0])
        xyxy[3] = xyxy[3]+0.1*(xyxy[3]-xyxy[1])
        # 将xyxy转换为正方形,以长变为基准
        if xyxy[2]-xyxy[0] > xyxy[3]-xyxy[1]: #宽大于长
            # 计算新的左上角和右下角坐标
            xyxy[1] = xyxy[1]-(xyxy[2]-xyxy[0]-(xyxy[3]-xyxy[1]))/2
            xyxy[3] = xyxy[3]+(xyxy[2]-xyxy[0]-(xyxy[3]-xyxy[1]))/2
        else: #长大于宽
            # 计算新的左上角和右下角坐标
            xyxy[0] = xyxy[0]-(xyxy[3]-xyxy[1]-(xyxy[2]-xyxy[0]))/2
            xyxy[2] = xyxy[2]+(xyxy[3]-xyxy[1]-(xyxy[2]-xyxy[0]))/2
        if xyxy[0]<0:
            xyxy[0]=0
        if xyxy[1]<0:
            xyxy[1]=0
        if xyxy[2]>_image.width:
            xyxy[2]=_image.width
        if xyxy[3]>_image.height:
            xyxy[3]=_image.height
        # 获取头的掩码
        # xyxy2 = image_util.get_max_xyxy(detections=detections,CLASSES=classes
        #                         ,reserves=["face"],_image=_image,broder=20)
        if remove_face: 
            # # 是否包含头
            # is_include_head = False
            # # 判断xyxy2是否有操过50%在xyxy中
            # # 计算交集的坐标
            # x1 = max(xyxy[0], xyxy2[0])
            # y1 = max(xyxy[1], xyxy2[1])
            # x2 = min(xyxy[2], xyxy2[2])
            # y2 = min(xyxy[3], xyxy2[3])
            # # 检查交集是否存在
            # if x1 < x2 and y1 < y2:
            #     # 计算交集面积
            #     intersection_area = (x2 - x1) * (y2 - y1)
            #     # 计算 xyxy2 的面积
            #     xyxy2_area = (xyxy2[2] - xyxy2[0]) * (xyxy2[3] - xyxy2[1])
            #     # 计算重合比例
            #     overlap_ratio = intersection_area / xyxy2_area
            #     if overlap_ratio > 0.5:
            #         # 将xyxy2的坐标合并到xyxy中
            #         is_include_head = True        
            # 获取头的掩码
            header_mask = [detections.mask[i] for i in range(len(detections.class_id)) if detections.class_id[i] is not None and classes[detections.class_id[i]] in ["face"]]
            # 将头的掩码应用于image
            if header_mask:
                total_head_mask = header_mask[0].copy()
                for mask in header_mask:
                        # 定义膨胀的核
                        kernel = np.ones((5,  ), np.uint8)  # 可以根据需要调整核的大小
                        mask = mask.astype(np.uint8)
                        # 进行膨胀操作
                        mask = cv2.dilate(mask, kernel, iterations=1) 
                        # 将掩码转换为布尔类型
                        mask_bool = mask.astype(bool)
                        # 将掩码应用于原始图像
                        total_head_mask[mask_bool] = 255
                    #    total_mask 去除 total_head_mask部分
                total_mask =  total_mask ^ total_head_mask

        T = torch.from_numpy(total_mask).to(torch.float32)
        _, _image = image_util.detail_optimization(_image,T,"VITMatte",6,6,0.15,0.99,True,"cuda",2.0)

        _image = image_util.bakground_withe(_image)
        # 保存原图
        original_image_path = os.path.join(original_folder_path, image_file)
        original_image_path = original_image_path.split(".")[0]+".png"
        #保持正方形
        image_util.convert_to_square(_image).save(original_image_path)
        _image = image_util.crop_image(_image,tuple(xyxy))
        _image = image_util.convert_to_fixed_size(image=_image,height=height,width=width)
        # 统一保存为png
        _image.save(output_image_path.split(".")[0]+".png")
        result.append({"image_name":image_file.split(".")[0]+".png","path":original_image_path,"xyxy":xyxy})
    return result

def process_image(url:str,
        filename:str,
        task_id:str="default",
        classes:list[str]=["face","clothing", "pants","shoes", "characters"],
        reserves:list[str] = ["clothing","pants"],
        remove_face:bool = True,
        threshold:float = 0.3,
        width:int = 768,
        height:int = 768,) -> dict:
    if remove_face :
        if "face" not in classes:
            classes.append("face")
    # 从图片的URL地址中获取文件名
    if filename is None or filename == "":
        filename = os.path.basename(url)
    # 构建输出图片的完整路径
    output_directory_new = os.path.join(output_directory, task_id)
    output_image_path = os.path.join(output_directory_new, filename)
    original_folder_path= os.path.join(output_directory_new, "original")
    if not os.path.exists(original_folder_path):
        os.makedirs(original_folder_path)
    # 读取输入图片
    # 修复图片加载方式
    response = requests.get(url, stream=True)
    response.raise_for_status()
    image = Image.open(response.raw)
    # 根据图片的EXIF信息，并旋转图片
    image = rotate_image_by_exif(image)
    image = image_util.pil2cv2(image)
    detections = dino_util.get_grounding_output(image=image, classes=classes,threshold=threshold)
    detections.mask = sam_util.segment(image, detections.xyxy)

    total_mask = detections.mask[0].copy()
    for _, mask in enumerate(detections.mask):
        # 将掩码转换为布尔类型
        mask_bool = mask.astype(bool)
        # 将掩码应用于原始图像
        total_mask[mask_bool] = 255
    _image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGBA))
    xyxy = image_util.get_max_xyxy(detections=detections,CLASSES=classes
                            ,reserves=reserves,_image=_image,broder=10)
    # xyxy[0] = xyxy[0]-0.1*min(xyxy[2]-xyxy[0],xyxy[3]-xyxy[1])
    # xyxy[1] = xyxy[1]-0.1*min(xyxy[2]-xyxy[0],xyxy[3]-xyxy[1])
    # 多漏点脚
    xyxy[2] = xyxy[2]+0.1*(xyxy[2]-xyxy[0])
    xyxy[3] = xyxy[3]+0.1*(xyxy[3]-xyxy[1])
    # 将xyxy转换为正方形,以长变为基准
    if xyxy[2]-xyxy[0] > xyxy[3]-xyxy[1]: #宽大于长
        # 计算新的左上角和右下角坐标
        xyxy[1] = xyxy[1]-(xyxy[2]-xyxy[0]-(xyxy[3]-xyxy[1]))/2
        xyxy[3] = xyxy[3]+(xyxy[2]-xyxy[0]-(xyxy[3]-xyxy[1]))/2
    else: #长大于宽
        # 计算新的左上角和右下角坐标
        xyxy[0] = xyxy[0]-(xyxy[3]-xyxy[1]-(xyxy[2]-xyxy[0]))/2
        xyxy[2] = xyxy[2]+(xyxy[3]-xyxy[1]-(xyxy[2]-xyxy[0]))/2
    if xyxy[0]<0:
        xyxy[0]=0
    if xyxy[1]<0:
        xyxy[1]=0
    if xyxy[2]>_image.width:
        xyxy[2]=_image.width
    if xyxy[3]>_image.height:
        xyxy[3]=_image.height
    # 获取头的掩码
    # xyxy2 = image_util.get_max_xyxy(detections=detections,CLASSES=classes
    #                         ,reserves=["face"],_image=_image,broder=20)
    if remove_face: 
        # # 是否包含头
        # is_include_head = False
        # # 判断xyxy2是否有操过50%在xyxy中
        # # 计算交集的坐标
        # x1 = max(xyxy[0], xyxy2[0])
        # y1 = max(xyxy[1], xyxy2[1])
        # x2 = min(xyxy[2], xyxy2[2])
        # y2 = min(xyxy[3], xyxy2[3])
        # # 检查交集是否存在
        # if x1 < x2 and y1 < y2:
        #     # 计算交集面积
        #     intersection_area = (x2 - x1) * (y2 - y1)
        #     # 计算 xyxy2 的面积
        #     xyxy2_area = (xyxy2[2] - xyxy2[0]) * (xyxy2[3] - xyxy2[1])
        #     # 计算重合比例
        #     overlap_ratio = intersection_area / xyxy2_area
        #     if overlap_ratio > 0.5:
        #         # 将xyxy2的坐标合并到xyxy中
        #         is_include_head = True        
        # 获取头的掩码
        header_mask = [detections.mask[i] for i in range(len(detections.class_id)) if detections.class_id[i] is not None and classes[detections.class_id[i]] in ["face"]]
        # 将头的掩码应用于image
        if header_mask:
            total_head_mask = header_mask[0].copy()
            for mask in header_mask:
                    # 定义膨胀的核
                    kernel = np.ones((5,  ), np.uint8)  # 可以根据需要调整核的大小
                    mask = mask.astype(np.uint8)
                    # 进行膨胀操作
                    mask = cv2.dilate(mask, kernel, iterations=1) 
                    # 将掩码转换为布尔类型
                    mask_bool = mask.astype(bool)
                    # 将掩码应用于原始图像
                    total_head_mask[mask_bool] = 255
                #    total_mask 去除 total_head_mask部分
            total_mask =  total_mask ^ total_head_mask

    T = torch.from_numpy(total_mask).to(torch.float32)
    _, _image = image_util.detail_optimization(_image,T,"VITMatte",6,6,0.15,0.99,True,"cuda",2.0)

    _image = image_util.bakground_withe(_image)
    # 保存原图
    original_image_path = os.path.join(original_folder_path, filename)
    original_image_path = original_image_path.split(".")[0]+".png"
    #保持正方形
    image_util.convert_to_square(_image).save(original_image_path)
    _image = image_util.crop_image(_image,tuple(xyxy))
    _image = image_util.convert_to_fixed_size(image=_image,height=height,width=width)
    # 统一保存为png
    _image.save(output_image_path.split(".")[0]+".png")
    return {"image_name":filename.split(".")[0]+".png","image":output_image_path.split(".")[0]+".png","original":original_image_path,"xyxy":xyxy}
    
# 更新图片
def update_image(folder_path:str,image:Image,image_name:str):
    # 构建输出图片的完整路径
    output_image_path = os.path.join(folder_path, image_name)
    # 保存图片到指定路径
    image.save(output_image_path)

def validate_image_path(image_path: str) -> bool:
    """
    Validates the image path to prevent directory traversal attacks. 
    Ensures the file exists and is within a restricted directory.
    """
    # Ensure the path is absolute and starts with a safe base directory
    if not os.path.isfile(image_path):
        return False
    return True

def get_media_type(image_path: str) -> str:
    """
    Determines the media type of the image based on its extension.
    """
    mime_type, _ = mimetypes.guess_type(image_path)
    return mime_type or "application/octet-stream"
    
def rotate_image_by_exif(image:Image):
    try:
        # 获取 EXIF 数据
        exif = image._getexif()
        if exif is not None:
            # 获取方向标签（Orientation 的 tag_id 是 274）
            orientation = exif.get(0x0112)
            if orientation is not None:
                # 根据方向值旋转图片
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
                # 其他情况无需旋转
    except AttributeError:
        pass  # 无 EXIF 数据
    return image