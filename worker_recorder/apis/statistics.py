# _*_ coding:utf-8 _*_
# @File  : statistics.py
# @Time  : 2021-01-05 15:00
# @Author: zizle

# 所有模块的数量

import datetime
import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from utils.encryption import decipher_user_token
from utils.time_handler import get_year_range
from apis.short_message.handler import get_messages, handle_detail_amount

statistics_router = APIRouter()


@statistics_router.get('/month-count/')
async def user_all_amount(user_token: str = Query(...)):
    user_id, access = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录已过期,请重新登录!')
    if 'admin' in access:
        user_id = 0
    # 获取起始日期
    # current_year = datetime.datetime.today().strftime('%Y-01-01')
    current_year = '2020-01-01'
    start_timestamp, end_timestamp = get_year_range(current_year)
    # 获取短讯通的数据
    short_messages = get_messages(start_timestamp, end_timestamp, user_id)
    # 按月分组处理数据
    statistics_messages = handle_detail_amount(pd.DataFrame(short_messages), 'year')
    # print(statistics_messages)
    msg_statistics_df = pd.DataFrame(statistics_messages)  # 转dataFrame计算每列的和
    if msg_statistics_df.empty:
        short_message_data = {
            'series_name': '短讯通',
            'area_color': '#2d8cf0',
            'series_data': []
        }
    else:
        # 删除author_id 和 username列
        del msg_statistics_df['author_id']
        del msg_statistics_df['username']
        # 求和
        msg_statistics_df.loc['col_sum'] = msg_statistics_df.sum()
        # 得到短讯通的数据
        short_message_amount = msg_statistics_df.tail(1).to_dict(orient='records')[0]
        short_message_data = {
            'series_name': '短讯通',
            'area_color': '#2d8cf0',
            'series_data': [{'month': k, 'count': v} for k, v in short_message_amount.items()]
        }
    data = [short_message_data]
    return {'message': '统计成功!', 'data': data}


