# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-01-13 08:11
# @Author: zizle

from fastapi import APIRouter
from .ondutymsg import onduty_api
from .statistics import statistics_api


onduty_message_router = APIRouter()
onduty_message_router.include_router(onduty_api)
onduty_message_router.include_router(statistics_api, prefix='/statistics')
