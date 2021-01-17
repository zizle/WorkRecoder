# _*_ coding:utf-8 _*_
# @File  : statistics.py
# @Time  : 2021-01-13 15:23
# @Author: zizle

# 收入指标统计(每个用户的客户数量和最新权益记录)

import datetime
import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from utils.time_handler import get_month_range, get_year_range, get_current_year
from utils.encryption import decipher_user_token
from .hanlder import get_customers_and_revenues, handle_customer_amount_revenue

statistics_api = APIRouter()


@statistics_api.get('/month/')
async def get_month_revenue(query_date: str = Query(...)):  # 按月统计每人的客户指标情况(留存与利息是累加和，权益为最新一条记录)
    start_timestamp, end_timestamp = get_month_range(query_date)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-%m-01`.')

    customers, revenues = get_customers_and_revenues(start_timestamp, end_timestamp, 0)
    result = handle_customer_amount_revenue(pd.DataFrame(customers), pd.DataFrame(revenues))
    return {'message': '月统计成功!', 'statistics': result}


@statistics_api.get('/year/')
async def get_month_revenue(query_date: str = Query(...)):  # 按年统计每人的客户指标情况(留存与利息是累加和，权益为最新一条记录)
    start_timestamp, end_timestamp = get_year_range(query_date)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-%m-01`.')

    customers, revenues = get_customers_and_revenues(start_timestamp, end_timestamp, 0)
    result = handle_customer_amount_revenue(pd.DataFrame(customers), pd.DataFrame(revenues))
    return {'message': '年统计成功!', 'statistics': result}


@statistics_api.get('/year-total/')  # 按年累计请求者的客户指标情况(请求者=admin则为所有人的客户情况)
async def get_user_year_total(user_token: str = Query(...)):
    # 解析出用户
    user_id, access = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期,请重新登录!')
    # 获取日期范围(1月28日(含)之后就显示新一年的)
    current_year = get_current_year()
    start_timestamp, end_timestamp = get_year_range(current_year)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-%m-01`.')
    is_admin = 0 if 'admin' in access else user_id
    customers, revenues = get_customers_and_revenues(start_timestamp, end_timestamp, is_admin)
    result = handle_customer_amount_revenue(pd.DataFrame(customers), pd.DataFrame(revenues))
    return {'message': '年统计成功!', 'statistics': result}
