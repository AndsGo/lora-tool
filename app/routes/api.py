import os
from fastapi import APIRouter,UploadFile,File,HTTPException,Query,Body
from fastapi.responses import FileResponse
from grounding_dino_util import get_grounding_output
from segment_anything_util import segment
from PIL import Image
import numpy as np
import app.entity.models as models
import app.util.tags_util as tags_util
import app.util.image_util as image_util

router = APIRouter(
    prefix="/api",
    tags=["api"],
    responses={404: {"description": "Not found"}},
)

@router.get("/image/grounding_output",summary="获取图片 grounding_output",description="获取图片 grounding_output")
async def grounding_output(request:models.GroundOutRequest=Query(...)):
    """
    获取图片 grounding_output"
    """
    # 只允许上传图片文件
    # 这里原代码中 image 未定义，推测需要修改逻辑，暂时注释掉
    # if image.content_type not in ["image/jpeg", "image/png"]:
    #     raise HTTPException(status_code=400, detail="Only image files are allowed")
    # prompt 不能为空
    if request.classes is None:
        raise HTTPException(status_code=400, detail="classes is empty")
   
    # image to np.ndarray
    try:
        # 循环读取图片
        request.image_folder = request.image_folder.strip()
        if request.image_folder == "":
            raise HTTPException(status_code=400, detail="image_folder is empty")
        
        # 新增：循环获取文件夹中的文件
        result = []
        for filename in os.listdir(request.image_folder):
            file_path = os.path.join(request.image_folder, filename)
            # 检查是否为文件
            if os.path.isfile(file_path):
                try:
                    image = Image.open(file_path)
                    # 检查图片格式
                    if image.format.lower() not in ["jpeg", "png"]:
                        continue
                    image_array = np.array(image)
                    detections = get_grounding_output(image_array, request.classes, request.model, request.threshold)
                    # 这里可以对结果进行进一步处理，例如存储到列表中
                    # print(f"Processed {filename}, result: {result}")
                    # detections convert to models.Detections()
                    d = models.Detections()
                    d.xyxy = detections.xyxy.tolist()
                    d.confidence = detections.confidence.tolist()
                    d.class_id = detections.class_id.tolist()
                    d.class_name = [request.classes[i] for i in detections.class_id]
                    result.append({"filename": filename, "detections": d})
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
        return models.BaseListResponse(code=10000,message="ok",data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"grounding_output error:{str(e)}")
    
@router.post("/image/segment",summary="图片分割",description="图片分割")
async def get_segment(image:UploadFile=File(...),request:models.GroundOutRequest=Query(...)):
    """
    图片分割"
    """
    # 只允许上传图片文件
    if image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only image(jpg/png) files are allowed")
    # image to np.ndarray
    try:
        image = Image.open(image.file)
        image_array = np.array(image)
        detections = get_grounding_output(image_array, request.classes, request.model, request.threshold)
        # 这里可以对结果进行进一步处理，例如存储到列表中
        detections.mask = segment(image_array, detections.xyxy)
        return models.BaseListResponse(code=10000,message="ok")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"segmentation error:{str(e)}")    
# 图片自动裁剪+打标签
@router.post("/image/auto",summary="图片自动裁剪+打标签",description="图片自动裁剪+打标签")
async def auto_crop(request:models.AutoRequest=Body(...)):
    try:
        data = image_util.process_image(request.url,request.filename,request.task_id, request.classes, request.reserves, request.remove_face, request.threshold, request.width, request.height)
        # 打标签
        tags = tags_util.get_one_tags(data["image"],request.classes,request.add_tags)
        # 去除前后空格
        tags = [tag.strip() for tag in tags]
        data["tags"] = tags
        return models.BaseDictResponse(code=10000,message="ok",data=data)
    except Exception as e:
        # e stack traceback
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"auto_crop error:{str(e)}")

# 图片归一化
@router.post("/image",summary="图片归一化",description="图片归一化")
async def normalize(request:models.NormalizeRequest=Body(...)):
    try:
        data =  image_util.process_images(request.input_folder, request.output_folder, request.classes, request.reserves, request.remove_face, request.threshold, request.width, request.height)
        return models.BaseListResponse(code=10000,message="ok",data=data)
    except Exception as e:
        # e stack traceback
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"normalize error:{str(e)}")

# 图片更新
@router.put("/image",summary="图片更新",description="图片更新")
async def update(folder_path:str=Query(...),image_name:str=Query(...),file:UploadFile=File(...)):
    # 判断file 是否为图片文件
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    try:
        # file to image
        image = Image.open(file.file)
        image_util.update_image(folder_path,image,image_name)
        return models.BaseResponse(code=10000,message="ok")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"update error:{str(e)}")

# 自动tags
@router.get("/tags",summary="自动tags",description="自动tags")
async def get_tags(request:models.TagsRequest=Query(...)):
    try:
        data = tags_util.get_tags(request.folder,request.remove_tags,request.add_tags)
        return models.TagsResponse(code=10000,message="ok",data=data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"tags error:{str(e)}")

# 更新tags
@router.put("/tags",summary="更新tags",description="更新tags")
async def update_tags(request:models.Tags=Body(...)):
    try:
        tags_util.save_tags(request)
        return models.BaseResponse(code=10000,message="ok")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"update_tags error:{str(e)}")
    
@router.get("/image", summary="显示图片", description="显示图片")
def show_image(image_path: str = Query(...)):
    try:
        # Validate the image path
        if not image_util.validate_image_path(image_path):
            raise HTTPException(status_code=404, detail="Image not found")

        # Validate the file format
        if not image_path.lower().endswith((".jpg", ".jpeg", ".png")):
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Determine the media type
        media_type = image_util.get_media_type(image_path)

        # Serve the file using FileResponse for efficiency
        return FileResponse(image_path, media_type=media_type)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
# 删除图片
@router.delete("/image",summary="删除图片",description="删除图片")
def delete_image(image_path:str=Query(...)):
    try:
        # 检查文件是否存在
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image not found")
        # 检查文件是否为图片文件
        if not image_path.lower().endswith((".jpg", ".jpeg", ".png")):
            raise HTTPException(status_code=400, detail="Invalid image format")
        # 删除图片文件
        os.remove(image_path)
        return models.BaseResponse(code=10000,message="ok")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"delete_image error:{str(e)}")

# 获取文件夹中的图片文件列表
@router.get("/image/list",summary="获取文件夹中的图片文件列表",description="获取文件夹中的图片文件列表")
def get_image_list(folder_path:str=Query(...)):
    try:
        # 读取文件夹中的所有图片文件
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        # 返回图片文件列表
        return models.BaseListResponse(code=10000,message="ok",data=image_files)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"get_image_list error:{str(e)}")
    
# 翻译
@router.get("/translate",summary="翻译",description="翻译")
async def translate(tags:list[str]=Query(default="",description="需要翻译原始的数组"),lang:str=Query("zh-CN",description="目标翻译的语言")):
    """
    lang: 目标翻译的语言
    {'afrikaans': 'af', 'albanian': 'sq', 'amharic': 'am', 'arabic': 'ar', 'armenian': 'hy', 'assamese': 'as', 'aymara': 'ay', 'azerbaijani': 'az', 'bambara': 'bm', 'basque': 'eu', 'belarusian': 'be', 'bengali': 'bn', 'bhojpuri': 'bho', 'bosnian': 'bs', 'bulgarian': 'bg', 'catalan': 'ca', 'cebuano': 'ceb', 'chichewa': 'ny', 'chinese (simplified)': 'zh-CN', 'chinese (traditional)': 'zh-TW', 'corsican': 'co', 'croatian': 'hr', 'czech': 'cs', 'danish': 'da', 'dhivehi': 'dv', 'dogri': 'doi', 'dutch': 'nl', 'english': 'en', 'esperanto': 'eo', 'estonian': 'et', 'ewe': 'ee', 'filipino': 'tl', 'finnish': 'fi', 'french': 'fr', 'frisian': 'fy', 'galician': 'gl', 'georgian': 'ka', 'german': 'de', 'greek': 'el', 'guarani': 'gn', 'gujarati': 'gu', 'haitian creole': 'ht', 'hausa': 'ha', 'hawaiian': 'haw', 'hebrew': 'iw', 'hindi': 'hi', 'hmong': 'hmn', 'hungarian': 'hu', 'icelandic': 'is', 'igbo': 'ig', 'ilocano': 'ilo', 'indonesian': 'id', 'irish': 'ga', 'italian': 'it', 'japanese': 'ja', 'javanese': 'jw', 'kannada': 'kn', 'kazakh': 'kk', 'khmer': 'km', 'kinyarwanda': 'rw', 'konkani': 'gom', 'korean': 'ko', 'krio': 'kri', 'kurdish (kurmanji)': 'ku', 'kurdish (sorani)': 'ckb', 'kyrgyz': 'ky', 'lao': 'lo', 'latin': 'la', 'latvian': 'lv', 'lingala': 'ln', 'lithuanian': 'lt', 'luganda': 'lg', 'luxembourgish': 'lb', 'macedonian': 'mk', 'maithili': 'mai', 'malagasy': 'mg', 'malay': 'ms', 'malayalam': 'ml', 'maltese': 'mt', 'maori': 'mi', 'marathi': 'mr', 'meiteilon (manipuri)': 'mni-Mtei', 'mizo': 'lus', 'mongolian': 'mn', 'myanmar': 'my', 'nepali': 'ne', 'norwegian': 'no', 'odia (oriya)': 'or', 'oromo': 'om', 'pashto': 'ps', 'persian': 'fa', 'polish': 'pl', 'portuguese': 'pt', 'punjabi': 'pa', 'quechua': 'qu', 'romanian': 'ro', 'russian': 'ru', 'samoan': 'sm', 'sanskrit': 'sa', 'scots gaelic': 'gd', 'sepedi': 'nso', 'serbian': 'sr', 'sesotho': 'st', 'shona': 'sn', 'sindhi': 'sd', 'sinhala': 'si', 'slovak': 'sk', 'slovenian': 'sl', 'somali': 'so', 'spanish': 'es', 'sundanese': 'su', 'swahili': 'sw', 'swedish': 'sv', 'tajik': 'tg', 'tamil': 'ta', 'tatar': 'tt', 'telugu': 'te', 'thai': 'th', 'tigrinya': 'ti', 'tsonga': 'ts', 'turkish': 'tr', 'turkmen': 'tk', 'twi': 'ak', 'ukrainian': 'uk', 'urdu': 'ur', 'uyghur': 'ug', 'uzbek': 'uz', 'vietnamese': 'vi', 'welsh': 'cy', 'xhosa': 'xh', 'yiddish': 'yi', 'yoruba': 'yo', 'zulu': 'zu'}
    """
    try:
        return models.BaseDictResponse(code=10000,message="ok",data=tags_util.translate_tags(tags,lang))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"translate_tags error:{str(e)}")

# 心跳检测
@router.get("/health",summary="心跳检测",description="心跳检测")
async def health():
    return models.BaseResponse(code=10000,message="ok")

# 获取名词列表
@router.get("/nouns",summary="获取名词列表",description="获取名词列表")
async def get_nouns(query:str=Query(default="",description="查询关键词")):
    try:
        return models.BaseListResponse(code=10000,message="ok",data=tags_util.get_noun_words(query=query))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"get_nouns error:{str(e)}")
    