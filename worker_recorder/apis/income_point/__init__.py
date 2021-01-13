# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-01-13 10:46
# @Author: zizle

from fastapi import APIRouter
from .income import income_api
from .statistics import statistics_api

income_point_router = APIRouter()
income_point_router.include_router(income_api)
income_point_router.include_router(statistics_api, prefix='/statistics')
