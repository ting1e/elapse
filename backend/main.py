from typing import Union
from sql_app.database import *
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sql_app.crud as CRUD
from fastapi.responses import FileResponse, HTMLResponse  # 响应html
from fastapi.staticfiles import StaticFiles # 设置静态目录
import os # 组装目录
import uvicorn as uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
from contextlib import asynccontextmanager
from cfg import cfg
sched = BackgroundScheduler()
sched.configure(timezone='Asia/Shanghai')

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("启动前执行")
    sched.add_job(CRUD.steam_games_update, CronTrigger.from_crontab('59 * * * *'),id='update_query',args=[cfg.steam_token,cfg.steam_id])
    sched.start()
    yield
    print("关闭后前执行")
    sched.shutdown()

app = FastAPI(lifespan=lifespan)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/dist", StaticFiles(directory=os.path.join(BASE_DIR, 'frontend/dist')), name="dist")
app.mount("/assets", StaticFiles(directory=os.path.join(BASE_DIR, 'frontend/dist/assets')), name="assets")

app.add_middleware(
    CORSMiddleware,    
    allow_origins= ["http://localhost:5173","http://localhost:8066"],    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],    
)
@app.get('/favicon.ico', include_in_schema=False)
def favicon():
    path = os.path.join(BASE_DIR, 'frontend/dist/favicon.ico')
    print(path)
    return FileResponse(path)

@app.get("/")
def index():
    html_path = os.path.join(BASE_DIR, 'frontend/dist/index.html')
    html_content = ''
    with open(html_path) as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/test_update")
def read_root():
    CRUD.steam_games_update(cfg.steam_token,cfg.steam_id)

@app.get("/test")
def get_record_year():
    return CRUD.GetPlayRecordYear()

@app.get("/emby_report")
def get_emby_report():
    url = cfg.emby_report
    sql = '''SELECT date(DateCreated) AS Date, SUM(PlayDuration) AS PlayTime
FROM PlaybackActivity
GROUP BY date(DateCreated)
ORDER BY date(DateCreated) ASC'''
    data = {
            "CustomQueryString": sql,
            "ReplaceUserId": False
        }
    res = requests.post(url,json=data,verify=False)
    return res.json()['results']


if __name__ == '__main__':
    uvicorn.run(app='main:app', host="127.0.0.1", port=8066, reload=True, )
    # nohup uvicorn main:app --host 127.0.0.1 --port 8066 --reload  &