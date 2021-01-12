# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-01-12 10:09
# @Author: zizle


from fastapi import APIRouter

from .abnormal import abnormal_api
from .statistics import statistics_api

abnormal_router = APIRouter()

abnormal_router.include_router(abnormal_api)
abnormal_router.include_router(statistics_api, prefix='/statistics')


