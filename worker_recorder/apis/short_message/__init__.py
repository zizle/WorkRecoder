# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2020-12-29 11:17
# @Author: zizle

# 短讯通

from fastapi import APIRouter

from .message import message_api
from .statistics import statistics_api

short_message_router = APIRouter()

short_message_router.include_router(message_api)
short_message_router.include_router(statistics_api, prefix='/statistics')

