# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-01-06 16:11
# @Author: zizle


from fastapi import APIRouter

from .strategy import strategy_api

strategy_router = APIRouter()


strategy_router.include_router(strategy_api)
