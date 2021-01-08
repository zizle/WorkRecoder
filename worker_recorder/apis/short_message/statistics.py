# _*_ coding:utf-8 _*_
# @File  : statistics.py
# @Time  : 2021-01-04 14:50
# @Author: zizle

# 短讯通统计API
# 1. 按月统计每人的短讯通数量和被标记数量
# 2. 按月统计每人每天的短讯通数量
# 3. 按年统计每人的短讯通数量和被标记数量
# 4. 按年统计每人每个月的短讯通数量
# 5. 按年累计请求者的短讯通数量(请求者=admin则为所有人的数量)

import datetime
import pandas as pd
from fastapi import APIRouter, Query, HTTPException

from utils.encryption import decipher_user_token
from utils.time_handler import get_year_range, get_month_range
from .handler import get_messages, handle_detail_amount, handle_amount_audit_rank

statistics_api = APIRouter()


@statistics_api.get('/month-rank/')  # 按月统计每人的短讯通数量和被标记数量
async def get_month_rank(query_date: str = Query(...)):
    start_timestamp, end_timestamp = get_month_range(query_date)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-%m-01`.')
    messages = get_messages(start_timestamp, end_timestamp, 0)
    amount_rank, quality_rank = handle_amount_audit_rank(pd.DataFrame(messages))
    return {'message': '统计成功!', 'amount_rank': amount_rank, 'quality_rank': quality_rank}


@statistics_api.get('/month-detail/')  # 按月统计每人每天的短讯通数量
async def get_month_detail(query_date: str = Query(...)):
    start_timestamp, end_timestamp = get_month_range(query_date)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-%m-01`.')
    messages = get_messages(start_timestamp, end_timestamp, 0)
    result = handle_detail_amount(pd.DataFrame(messages), 'month')  # 转为DataFrame进行处理
    return {'message': '统计成功!', 'month_detail': result}


@statistics_api.get('/year-rank/')  # 按年统计每人的短讯通数量和被标记数量
async def get_year_rank(query_date: str = Query(...)):
    start_timestamp, end_timestamp = get_year_range(query_date)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-01-01`.')
    message = get_messages(start_timestamp, end_timestamp, 0)
    # 转为DataFrame处理
    message_df = pd.DataFrame(message)
    if message_df.empty:
        return {'message': '统计成功!', 'amount_rank': [], 'quality_rank': []}
    amount_rank, quality_rank = handle_amount_audit_rank(message_df)
    return {'message': '统计成功!', 'amount_rank': amount_rank, 'quality_rank': quality_rank}


@statistics_api.get('/year-detail/')  # 按年统计每人每个月的短讯通数量
async def get_month_detail(query_date: str = Query(...)):
    start_timestamp, end_timestamp = get_year_range(query_date)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-01-01`.')
    messages = get_messages(start_timestamp, end_timestamp, 0)
    result = handle_detail_amount(pd.DataFrame(messages), 'year')  # 转为DataFrame进行处理
    return {'message': '查询成功!', 'year_detail': result}


@statistics_api.get('/year-total/')  # 按年累计请求者的短讯通数量(请求者=admin则为所有人的数量)
async def get_user_year_total(user_token: str = Query(...)):
    # 解析出用户
    user_id, access = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期,请重新登录!')
    # 获取日期范围
    current_year = datetime.datetime.today().strftime('%Y-01-01')
    current_year = '2020-01-01'
    start_timestamp, end_timestamp = get_year_range(current_year)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-01-01`.')
    message = get_messages(start_timestamp, end_timestamp, 0)
    message_df = pd.DataFrame(message)
    if message_df.empty:
        return {'message': '统计成功!', 'total_count': 0, 'percent': '-'}
    total_count = message_df.shape[0]
    if 'admin' in access:
        user_count = total_count
        percent = 100 if total_count else 0
    else:
        # 选取用户的短讯通
        user_message_df = message_df[message_df['author_id'] == user_id]
        user_count = user_message_df.shape[0]
        percent = round(user_count / total_count * 100, 2) if total_count else 0
    return {'message': '统计成功!', 'total_count': user_count, 'percent': percent}
