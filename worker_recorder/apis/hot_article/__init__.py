# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-01-12 15:26
# @Author: zizle

from fastapi import APIRouter
from .article import article_api
from .statistics import statistics_api

article_router = APIRouter()

article_router.include_router(article_api)
article_router.include_router(statistics_api, prefix='/statistics')
