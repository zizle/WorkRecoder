# _*_ coding:utf-8 _*_


# 品种的API
# 1. 管理员添加品种
# 2. 管理员删除品种
# 3. 管理员修改品种的信息

from fastapi import APIRouter

from .variety import variety_api

variety_router = APIRouter()

variety_router.include_router(variety_api)  # 品种接口
