# _*_ coding:utf-8 _*_
# @File  : statistics.py
# @Time  : 2021-01-13 15:23
# @Author: zizle

# 收入指标统计(每个用户的客户数量和最新权益记录)

import pandas as pd
from fastapi import APIRouter
from .hanlder import get_customers, get_customer_revenue, handle_customer_amount_revenue

statistics_api = APIRouter()


@statistics_api.get('/')
async def statistics_customer_revenue():  # 统计每个用户的客户数量和客户权益
    customers = get_customers()
    revenues = get_customer_revenue()
    result = handle_customer_amount_revenue(pd.DataFrame(customers), pd.DataFrame(revenues))
    return {'message': '统计成功!', 'statistics': result}



