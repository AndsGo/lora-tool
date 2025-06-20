import uvicorn
import logging
from fastapi_offline import FastAPIOffline
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routes import api

app = FastAPIOffline()
router = APIRouter()


# 前端主页面
@router.get("/ui", summary="前端页面")
async def get_index():
    return FileResponse("app/ui/index.html") 


# 前端静态资源
app.mount("/static/", StaticFiles(directory="app/ui/static"), name="static")

# API接口
app.include_router(router)
app.include_router(api.router)



if __name__ == "__main__": 
    # 后台线程 自动打开127.0.0.1:8000 页面
    # import webbrowser
    # import threading
    # def open_browser():
    #     import time
    #     time.sleep(2)
    #     webbrowser.open("http://127.0.0.1:8000/ui")
    # threading.Thread(target=open_browser).start()
    logging.Logger("请访问:http://127.0.0.1:8000/ui")
    print("请访问:http://127.0.0.1:8000/ui")
    # 设置只允许本地访问，端口为8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
    

