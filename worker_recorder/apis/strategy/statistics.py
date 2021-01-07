# _*_ coding:utf-8 _*_
# @File  : statistics.py
# @Time  : 2021-01-07 11:03
# @Author: zizle

# 投顾策略的统计

# 1. 按月统计每人的投顾策略数量、成功量、成功率、收益、收益率
# 2. 按年统计每人的投顾策略数量、成功量、成功率、收益、收益率


import pandas as pd
from fastapi import APIRouter, Query, HTTPException

from utils.time_handler import get_month_range, get_year_range
from .handler import get_strategy, handle_strategy_amount_rate

statistics_api = APIRouter()


@statistics_api.get('/month/')  # 按月统计每人的投顾策略数量、成功量、成功率、收益、收益率
async def get_month_statistics(query_date: str = Query(...)):
    start_timestamp, end_timestamp = get_month_range(query_date)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-%m-01`.')
    strategies = get_strategy(start_timestamp, end_timestamp, 0)
    # 转为DataFrame进行数据处理
    result = handle_strategy_amount_rate(pd.DataFrame(strategies))
    return {'message': '统计成功!', 'statistics': result}


@statistics_api.get('/year/')  # 按年统计每人的投顾策略数量、成功量、成功率、收益、收益率
async def get_year_statistics(query_date: str = Query(...)):
    start_timestamp, end_timestamp = get_year_range(query_date)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-01-01`.')
    strategies = get_strategy(start_timestamp, end_timestamp, 0)
    # 转为DataFrame进行数据处理
    result = handle_strategy_amount_rate(pd.DataFrame(strategies))
    return {'message': '统计成功!', 'statistics': result}
