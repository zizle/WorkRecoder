# _*_ coding:utf-8 _*_
# @File  : strategy.py
# @Time  : 2021-01-06 16:14
# @Author: zizle


# 投顾策略api
# 1. POST-用户添加一条策略

import datetime
from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from utils.encryption import decipher_user_token
from db import DBWorker
from .validate_models import StrategyAddItem

strategy_api = APIRouter()


@strategy_api.post('/')
async def add_strategy(strategy_item: StrategyAddItem = Body(...)):
    print(strategy_item)
    # 解析用户保存数据
    user_id, access = decipher_user_token(strategy_item.user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录已过期,请重新登录!')
    now_timestamp = int(datetime.datetime.now().timestamp())
    strategy_add = jsonable_encoder(strategy_item)
    strategy_add['create_time'] = now_timestamp
    strategy_add['join_time'] = now_timestamp
    strategy_add['update_time'] = now_timestamp
    strategy_add['author_id'] = user_id
    del strategy_add['user_token']
    with DBWorker() as (_, cursor):
        cursor.execute(
            "INSERT INTO work_strategy (create_time,join_time,update_time,author_id,content,variety_en,contract,"
            "direction,hands,open_price,close_price,profit,note) VALUES (%(create_time)s,%(join_time)s,%(update_time)s,"
            "%(author_id)s,%(content)s,%(variety_en)s,%(contract)s,%(direction)s,%(hands)s,%(open_price)s,"
            "%(close_price)s,%(profit)s,%(note)s);",
            strategy_add
        )
    return {'message': '添加成功!'}

