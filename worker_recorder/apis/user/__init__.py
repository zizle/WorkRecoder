# _*_ coding:utf-8 _*_

# 用户模块

from fastapi import APIRouter
from .user import user_api

user_router = APIRouter()

user_router.include_router(user_api)  # 用户接口
