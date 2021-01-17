# _*_ coding:utf-8 _*_
# @File  : statistics.py
# @Time  : 2021-01-12 08:00
# @Author: zizle

# 统计非常态工作记录

import datetime
import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from utils.time_handler import get_month_range, get_year_range, get_current_year
from utils.encryption import decipher_user_token
from .hanlder import get_abnormal_work, handle_abnormal_amount_score, handle_abnormal_work_amount

statistics_api = APIRouter()


@statistics_api.get('/month/')  # 按月统计每人的投资方案数量
async def get_month_statistics(query_date: str = Query(...)):
    start_timestamp, end_timestamp = get_month_range(query_date)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-%m-01`.')
    investments = get_abnormal_work(start_timestamp, end_timestamp, 0)
    result = handle_abnormal_amount_score(pd.DataFrame(investments))
    return {'message': '统计成功!', 'statistics': result}


@statistics_api.get('/year/')  # 按年统计每人的投顾策略数量、成功量、成功率、收益、收益率
async def get_year_statistics(query_date: str = Query(...)):
    start_timestamp, end_timestamp = get_year_range(query_date)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-01-01`.')
    strategies = get_abnormal_work(start_timestamp, end_timestamp, 0)
    # 转为DataFrame进行数据处理
    result = handle_abnormal_amount_score(pd.DataFrame(strategies))
    return {'message': '统计成功!', 'statistics': result}


@statistics_api.get('/year-total/')  # 按年累计请求者非常规工作数量(请求者=admin则为所有人的数量)
async def get_user_year_total(user_token: str = Query(...)):
    # 解析出用户
    user_id, access = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期,请重新登录!')
    # 获取日期范围(1月28日(含)之后就显示新一年的)
    current_year = get_current_year()
    start_timestamp, end_timestamp = get_year_range(current_year)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-01-01`.')

    records = get_abnormal_work(start_timestamp, end_timestamp, 0)
    record_df = pd.DataFrame(records)
    if record_df.empty:
        return {'message': '统计成功!', 'total_count': 0, 'percent': '-'}
    total_count = record_df.shape[0]
    if 'admin' in access:
        detail_count_data = handle_abnormal_work_amount(record_df, 'year')
        user_count = total_count
        percent = 100 if total_count else 0
    else:
        # 选取用户的非常规工作
        user_record_df = record_df[record_df['author_id'] == user_id]
        detail_count_data = handle_abnormal_work_amount(user_record_df, 'year')
        user_count = user_record_df.shape[0]
        percent = round(user_count / total_count * 100, 2) if total_count else 0
    return {'message': '统计成功!', 'total_count': user_count, 'percent': percent, 'month_count': detail_count_data}
