# _*_ coding:utf-8 _*_

from fastapi import APIRouter

# 各模块的api router
from apis.user import user_router                           # 用户api
from apis.variety import variety_router                     # 品种的api
from apis.short_message import short_message_router         # 短信通api
from apis.strategy import strategy_router                   # 投顾策略api
from apis.investment import investment_router               # 投资方案api
from apis.abnormal import abnormal_router                   # 非常规工作api
from apis.hot_article import article_router                 # 热点文章api
from apis.statistics import statistics_router


routers = APIRouter()

routers.include_router(statistics_router, prefix='/statistics')
routers.include_router(user_router, prefix='/user')
routers.include_router(variety_router, prefix='/variety')
routers.include_router(short_message_router, prefix='/shtmsg')
routers.include_router(strategy_router, prefix='/strategy')
routers.include_router(investment_router, prefix='/investment')
routers.include_router(abnormal_router, prefix='/abnormal')
routers.include_router(article_router, prefix='/article')
