# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-01-18 13:43
# @Author: zizle

# 专题研究
# 2021年业务已合并到热点文章，所以只提供一个查询接口

from fastapi import APIRouter
from .monographic import monographic_api

monographic_router = APIRouter()
monographic_router.include_router(monographic_api)

