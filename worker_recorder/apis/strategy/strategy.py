# _*_ coding:utf-8 _*_
# @File  : strategy.py
# @Time  : 2021-01-06 16:14
# @Author: zizle


# 投顾策略api
# 1. POST-用户添加一条策略
# 2. 查询用户指定日期范围的策略并分页(支持关键内容检索)
# 3. 用户或管理者删除一条投顾策略记录

import datetime
import pandas as pd
from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from utils.encryption import decipher_user_token
from utils.constants import VARIETY_CN
from db import DBWorker
from .validate_models import StrategyAddItem, QueryStrategyItem, ModifyStrategyItem
from apis.tools import validate_operate_user, validate_date_range, filter_records
from .handler import handle_strategy_amount_rate

strategy_api = APIRouter()


def handle_strategy_item(item):
    item['create_time'] = datetime.datetime.fromtimestamp(item['create_time']).strftime('%Y-%m-%d')
    item['join_time'] = datetime.datetime.fromtimestamp(item['join_time']).strftime('%Y-%m-%d %H:%M:%S')
    item['update_time'] = datetime.datetime.fromtimestamp(item['update_time']).strftime('%Y-%m-%d %H:%M:%S')
    item['contract_name'] = VARIETY_CN.get(item['variety_en'], '') + item['contract']
    return item


@strategy_api.post('/add/')  # POST-用户添加一条策略
async def add_strategy(strategy_item: StrategyAddItem = Body(...)):
    # 解析用户保存数据
    user_id, access = decipher_user_token(strategy_item.user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录已过期,请重新登录!')
    now_timestamp = int(datetime.datetime.now().timestamp())
    strategy_add = jsonable_encoder(strategy_item)
    strategy_add['create_time'] = int(datetime.datetime.strptime(strategy_item.create_time, '%Y-%m-%d').timestamp())
    strategy_add['join_time'] = now_timestamp
    strategy_add['update_time'] = now_timestamp
    strategy_add['author_id'] = user_id
    del strategy_add['user_token']
    with DBWorker() as (_, cursor):
        cursor.execute(
            "INSERT INTO work_strategy (create_time,join_time,update_time,author_id,content,variety_en,contract,"
            "direction,hands,open_price,close_price,profit,is_running,note) "
            "VALUES (%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,%(content)s,%(variety_en)s,"
            "%(contract)s,%(direction)s,%(hands)s,%(open_price)s,"
            "%(close_price)s,%(profit)s,%(is_running)s,%(note)s);",
            strategy_add
        )
    return {'message': '添加成功!'}


@strategy_api.post('/')  # 查询用户指定日期范围的策略并分页(支持关键内容检索)
async def query_strategy(query_item: QueryStrategyItem = Body(...)):
    # 验证用户
    audit = 'strategy' if query_item.is_audit else None
    user_id, is_audit = validate_operate_user(query_item.user_token, audit)
    start_timestamp, end_timestamp = validate_date_range(query_item.start_date, query_item.end_date)
    # 查询数据
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT stb.id,stb.create_time,stb.join_time,stb.update_time,stb.author_id,usertb.username,stb.variety_en,"
            "stb.contract, stb.content,stb.direction,stb.hands,stb.open_price,stb.close_price,stb.profit,"
            "stb.is_running,stb.note "
            "FROM work_strategy AS stb "
            "INNER JOIN user_user AS usertb ON usertb.id=stb.author_id "
            "WHERE stb.create_time>%s AND stb.create_time<=%s AND IF(1=%s,TRUE,stb.author_id=%s) "
            "ORDER BY stb.create_time DESC;",
            (start_timestamp, end_timestamp, is_audit, user_id)
        )
        strategies = cursor.fetchall()
        # 查询总数量
        cursor.execute(
            "SELECT stb.id,stb.author_id,stb.content "
            "FROM work_strategy AS stb "
            "INNER JOIN user_user AS usertb ON usertb.id=stb.author_id "
            "WHERE stb.create_time>%s AND stb.create_time<=%s AND IF(1=%s,TRUE,stb.author_id=%s);",
            (start_timestamp, end_timestamp, is_audit, user_id)
        )
        total_strategies = cursor.fetchall()
    strategies, total_strategies = filter_records(
        is_audit, query_item.req_staff, query_item.keyword, 'content', strategies, total_strategies)
    # 统计计算结果数据
    statistics_result = handle_strategy_amount_rate(pd.DataFrame(strategies))
    # 截取数据(分页)
    strategies = strategies[(query_item.page - 1) * query_item.page_size: query_item.page_size * query_item.page]
    # 处理数据内容
    strategies = list(map(handle_strategy_item, strategies))
    return {'message': '获取投顾策略成功!',
            'strategies': strategies, 'page': query_item.page, 'total_count': len(total_strategies),
            'statistics': statistics_result}


@strategy_api.put('/modify/{strategy_id}/')
async def modify_strategy_record(strategy_id: int, modify_item: ModifyStrategyItem = Body(...)):
    user_id, is_audit = validate_operate_user(modify_item.user_token)
    # 修改数据
    update_timestamp = int(datetime.datetime.now().timestamp())
    with DBWorker() as (_, cursor):
        cursor.execute(
            "UPDATE work_strategy SET update_time=%s,open_price=%s,close_price=%s,profit=%s,note=%s,is_running=%s "
            "WHERE id=%s AND author_id=%s;",
            (update_timestamp, modify_item.open_price, modify_item.close_price, modify_item.profit, modify_item.note,
             modify_item.is_running, strategy_id, user_id)
        )
    return {'message': '修改成功!', 'strategy': modify_item}


@strategy_api.delete('/remove/{strategy_id}/')  # 用户或管理者删除一条投顾策略记录
async def delete_strategy_record(strategy_id: int, user_token: str = Query(...)):
    user_id, is_audit = validate_operate_user(user_token)
    # 删除数据
    with DBWorker() as (_, cursor):
        cursor.execute('SELECT id,author_id FROM work_strategy WHERE id=%s;', (strategy_id, ))
        strategy_record = cursor.fetchone()
        if strategy_record:
            if is_audit != 1 and strategy_record['author_id'] != user_id:
                raise HTTPException(status_code=403, detail='不能删除他人的数据记录!')
            # 删除记录
            cursor.execute(
                "DELETE FROM work_strategy WHERE id=%s AND IF(1=%s,TRUE,author_id=%s) LIMIT 1;",
                (strategy_id, is_audit, user_id)
            )
            return {'message': '删除成功!'}
        else:
            raise HTTPException(status_code=400, detail='数据不存在!')
