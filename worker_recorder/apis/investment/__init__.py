# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-01-11 08:47
# @Author: zizle

from fastapi import APIRouter
from .investment import investment_api


investment_router = APIRouter()

investment_router.include_router(investment_api)
