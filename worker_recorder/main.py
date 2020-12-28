# _*_ coding:utf-8 _*_


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from settings import STATICS_STORAGE
from routers import routers

app = FastAPI()

app.mount("/static/", StaticFiles(directory=STATICS_STORAGE), name="staticFiles")

# 支持跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routers, prefix='/api')

