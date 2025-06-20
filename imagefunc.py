from layer_style.imagefunc import *
def detail_optimization(_image, _mask, detail_method, detail_erode, detail_dilate,
                        black_point, white_point, process_detail,
                        device, max_megapixels):
    """
    对图像的细节进行优化处理。

    此函数根据传入的细节处理方法，对输入的图像和掩码进行细节优化。
    支持多种细节处理方法，如 GuidedFilter、PyMatting 和 VITMatte。

    Args:
        _image (PIL.Image): 输入的图像。
        _mask (torch.Tensor): 输入的掩码。
        detail_method (str): 细节处理方法，可选值为 'GuidedFilter', 'PyMatting', 'VITMatte(local)' 等。
        detail_erode (int): 腐蚀操作的参数。
        detail_dilate (int): 膨胀操作的参数。
        black_point (float): 直方图重映射的黑点参数。
        white_point (float): 直方图重映射的白点参数。
        process_detail (bool): 是否进行细节处理的标志。
        device (str): 设备类型，如 'cuda' 或 'cpu'。
        max_megapixels (float): 最大处理像素数。

    Returns:
        tuple: 优化后的掩码 (PIL.Image) 和图像 (PIL.Image)。
    """
    # 将 PIL 图像转换为张量
    i = pil2tensor(_image)
    # 判断是否仅使用本地文件
    if detail_method == 'VITMatte(local)':
        local_files_only = True
    else:
        local_files_only = False
    # 计算细节处理范围
    detail_range = detail_erode + detail_dilate
    # 如果需要进行细节处理
    if process_detail:
        # 使用 GuidedFilter 方法进行细节处理
        if detail_method == 'GuidedFilter':
            # 应用引导滤波对掩码进行处理
            _mask = guided_filter_alpha(i, _mask, detail_range // 6 + 1)
            # 将处理后的张量掩码转换为 PIL 图像，并进行直方图重映射
            _mask = tensor2pil(histogram_remap(_mask, black_point, white_point))
        # 使用 PyMatting 方法进行细节处理
        elif detail_method == 'PyMatting':
            # 对掩码边缘进行细节处理，并将结果转换为 PIL 图像
            _mask = tensor2pil(mask_edge_detail(i, _mask, detail_range // 8 + 1, black_point, white_point))
        # 使用其他方法（如 VITMatte）进行细节处理
        else:
            # 生成 VITMatte 的 trimap
            _trimap = generate_VITMatte_trimap(_mask, detail_erode, detail_dilate)
            # 生成 VITMatte 掩码
            _mask = generate_VITMatte(_image, _trimap, local_files_only=local_files_only, device=device, max_megapixels=max_megapixels)
            # 将处理后的掩码转换为张量，进行直方图重映射，再转换回 PIL 图像
            _mask = tensor2pil(histogram_remap(pil2tensor(_mask), black_point, white_point))
    # 如果不需要进行细节处理
    else:
        # 将掩码转换为图像
        _mask = mask2image(_mask)
    # 将处理后的图像和掩码合并为 RGBA 图像
    _image = RGB2RGBA(tensor2pil(i).convert('RGB'), _mask.convert('L'))
    # 返回处理后的掩码和图像
    return _mask, _image

# 图片变白底
def bakground_withe(_image):
    # 图片变白底
    # 转换为RGBA格式
    _image = _image.convert("RGBA")
    # 获取图像的宽度和高度
    width, height = _image.size
    # 创建一个新的RGBA图像，背景为白色
    white_background = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    # 将原始图像与白色背景进行合成
    result = Image.alpha_composite(white_background, _image)
    return result

def get_max_xyxy(CLASSES, reserves, detections, _image,broder=5) ->list:
    """
    根据指定类别筛选检测结果，并裁剪出这些类别对应区域的并集最大区域图像。

    Args:
        CLASSES (list): 类别名称列表，用于根据检测结果中的类别索引获取类别名称。
        reserves (list): 要保留的类别名称列表，用于筛选检测结果。
        detections (object): 检测结果对象，包含边界框信息和类别索引等。
        _image (PIL.Image): 待处理的原始图像。
        broder (int, optional): 裁剪边界的大小。默认为 5。

   """
    # 初始化一个空列表，用于存储符合指定类别条件的检测结果的索引
    clothing_pants_indices = []
    # 遍历所有检测结果
    for i, _ in enumerate(detections):
        class_id = detections.class_id[i]
        if class_id is None:
            continue
        # 检查当前检测结果的类别是否在要保留的类别列表中
        if class_id < len(CLASSES) and CLASSES[class_id] in reserves:
            # 如果是，则将该检测结果的索引添加到列表中
            clothing_pants_indices.append(i)

    # 检查是否有符合条件的检测结果
    if clothing_pants_indices:
        # 提取这些检测结果的边界框
        clothing_pants_boxes = detections.xyxy[clothing_pants_indices]

        # 找出共同的并集最大区域
        # 计算所有边界框左上角 x 坐标的最小值
        min_x = int(np.min(clothing_pants_boxes[:, 0]))-broder
        # 计算所有边界框左上角 y 坐标的最小值
        min_y = int(np.min(clothing_pants_boxes[:, 1]))-broder
        # 计算所有边界框右下角 x 坐标的最大值
        max_x = int(np.max(clothing_pants_boxes[:, 2]))+broder
        # 计算所有边界框右下角 y 坐标的最大值
        max_y = int(np.max(clothing_pants_boxes[:, 3]))+broder

        # 检查边界是否超出图像边界
        if min_x < 0:
            min_x = 0
        if min_y < 0:
            min_y = 0
        if max_x > _image.width:
            max_x = _image.width
        if max_y > _image.height:
            max_y = _image.height
    else:
        min_x = 0
        min_y = 0
        max_x = _image.width
        max_y = _image.height
    return [min_x, min_y, max_x, max_y]

def crop_max_xyxy(CLASSES, reserves, detections, _image,broder=5):
    """
    根据指定类别筛选检测结果，并裁剪出这些类别对应区域的并集最大区域图像。

    Args:
        CLASSES (list): 类别名称列表，用于根据检测结果中的类别索引获取类别名称。
        reserves (list): 要保留的类别名称列表，用于筛选检测结果。
        detections (object): 检测结果对象，包含边界框信息和类别索引等。
        _image (PIL.Image): 待处理的原始图像。
        broder (int, optional): 裁剪边界的大小。默认为 5。

    Returns:
        PIL.Image: 裁剪后的图像。如果未检测到指定类别，返回 None。
    """
    xyxy = get_max_xyxy(CLASSES, reserves, detections, _image,broder)
    # 裁剪图像
    cropped_image = _image.crop(tuple(xyxy))
    return cropped_image

def crop_image(_image:Image, xyxy:tuple):
    """
    根据指定的边界框裁剪图像。"
    """
    # 裁剪图像
    cropped_image = _image.crop(xyxy)
    return cropped_image
   
# 将图片转化为固定宽高比的图片，多出的部分用白色填充
def convert_to_square(image:Image):
    # 获取图像的宽度和高度
    width, height = image.size
    # 计算最大边的长度
    max_size = max(width, height)
    # 创建一个新的正方形图像，背景为白色
    new_image = Image.new("RGB", (max_size, max_size), (255, 255, 255))
    # 计算粘贴位置
    paste_position = ((max_size - width) // 2, (max_size - height) // 2)
    # 将原始图像粘贴到新图像的中心
    new_image.paste(image, paste_position)
    # 返回转换后的正方形图像
    return new_image

def convert_to_square_cv2(image:cv2.Mat):
    # 获取图像的宽度和高度
    height, width = image.shape[:2]
    # 计算最大边的长度
    max_size = max(width, height)
    # 创建一个新的正方形图像，背景为白色
    new_image = np.ones((max_size, max_size, 3), dtype=np.uint8) * 255
    # 计算粘贴位置
    paste_position = ((max_size - width) // 2, (max_size - height) // 2)
    # 将原始图像粘贴到新图像的中心
    new_image[paste_position[1]:paste_position[1]+height, paste_position[0]:paste_position[0]+width] = image
    # 返回转换后的正方形图像
    return new_image

# 将图片转换为固定宽高的图片，多余的部分用白色填充
def convert_to_fixed_size(image:Image, width:int, height:int):
    # 获取图像的宽度和高度
    image_width, image_height = image.size
    # 计算缩放比例
    scale = min(width / image_width, height / image_height)
    # 计算新的宽度和高度
    new_width = int(image_width * scale)
    new_height = int(image_height * scale)
    # 计算粘贴位置
    paste_position = ((width - new_width) // 2, (height - new_height) // 2)
    # 创建一个新的固定大小的图像，背景为白色
    new_image = Image.new("RGB", (width, height), (255, 255, 255))
    # 将原始图像粘贴到新图像的中心
    new_image.paste(image.resize((new_width, new_height), Image.LANCZOS), paste_position)
    # 返回转换后的固定大小图像
    return new_image


# 将等比缩放到固定高度
def convert_to_fixed_height(image:Image, height:int):
    # 获取图像的宽度和高度
    image_width, image_height = image.size
    # 计算缩放比例
    scale = height / image_height
    # 计算新的宽度和高度
    new_width = int(image_width * scale)
    new_height = int(image_height * scale)
    # 创建一个新的固定大小的图像，背景为白色
    new_image = Image.new("RGB", (new_width, new_height), (255, 255, 255))
    # 将原始图像粘贴到新图像的中心
    new_image.paste(image.resize((new_width, new_height), Image.LANCZOS), (0, 0))
    # 返回转换后的固定大小图像
    return new_image