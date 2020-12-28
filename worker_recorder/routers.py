# _*_ coding:utf-8 _*_

from fastapi import APIRouter

# 各模块的api router
from apis.user import user_router        # 用户API
from apis.variety import variety_router  # 品种的api


routers = APIRouter()

routers.include_router(user_router, prefix='/user')
routers.include_router(variety_router, prefix='/variety')
