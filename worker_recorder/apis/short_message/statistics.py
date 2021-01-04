# _*_ coding:utf-8 _*_
# @File  : statistics.py
# @Time  : 2021-01-04 14:50
# @Author: zizle

# 短讯通统计API

import datetime
import pandas as pd
from fastapi import APIRouter, Query, HTTPException

from db import DBWorker

statistics_api = APIRouter()


def get_next_month_date(c_date: datetime.datetime):
    year = c_date.year
    month = c_date.month
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    return datetime.datetime.strptime('{}-{}-01'.format(year, month), '%Y-%m-01')


def get_messages(query_date: str):
    try:
        query_date = datetime.datetime.strptime(query_date, '%Y-%m-01')
    except ValueError:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-%m-01`.')
    start_timestamp = int(query_date.timestamp())
    end_timestamp = int(get_next_month_date(query_date).timestamp())
    # 查询数据
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT msgtb.id,msgtb.create_time,msgtb.author_id,usertb.username,msgtb.audit_mind "
            "FROM work_short_message AS msgtb "
            "INNER JOIN user_user AS usertb ON msgtb.author_id=usertb.id "
            "WHERE msgtb.create_time>=%s AND msgtb.create_time<%s;",
            (start_timestamp, end_timestamp)
        )
        messages = cursor.fetchall()
    return messages


@statistics_api.get('/month-rank/')
async def get_month_rank(query_date: str = Query(...)):
    messages = get_messages(query_date)
    # print(message)
    # 使用pandas进行目标数据处理
    message_df = pd.DataFrame(messages)
    if message_df.empty:
        return {'message': '统计成功!', 'amount_rank': [], 'quality_rank': []}
    # 以作者分组统计
    author_count_df = message_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg({'count': 'count'})
    author_count_df['rank'] = author_count_df['count'].rank(method='dense', ascending=False).astype(int)
    amount_rank = author_count_df.to_dict(orient='records')
    # 以作者分组,audit_mind!=0标记统计
    # 筛选出audit_mind != 0的
    message_audit_df = message_df[~(message_df['audit_mind'] == 0)]
    # 对此进行分组统计
    audit_mind_count_df = message_audit_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg({'count': 'count'})
    audit_mind_count_df['rank'] = audit_mind_count_df['count'].rank(method='dense', ascending=False).astype(int)
    quality_rank = audit_mind_count_df.to_dict(orient='records')

    return {'message': '统计成功!', 'amount_rank': amount_rank, 'quality_rank': quality_rank}


@statistics_api.get('/month-detail/')
async def get_month_detail(query_date: str = Query(...)):
    messages = get_messages(query_date)
    # 转为DataFrame进行处理
    message_df = pd.DataFrame(messages)
    if message_df.empty:
        return {'message': '统计成功!', 'detail_data': []}
    # 以人员每日进行分组统计
    author_date_count_df = message_df.groupby(['author_id', 'username', 'create_time'], as_index=False)['author_id'].agg({'count': 'count'})
    # 转化日期
    author_date_count_df['create_time'] = author_date_count_df['create_time'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d'))
    author_date_count_df['author_id'] = author_date_count_df['author_id'].astype(int)
    author_date_count_df['count'] = author_date_count_df['count'].astype(int)
    # 再次根据作者分组
    result = []
    for name, group in author_date_count_df.groupby(['author_id', 'username']):
        user_data = {'author_id': int(name[0]), 'username': str(name[1])}
        group_df = group.set_index('create_time').reset_index()  # 得到日期对应的作者的数量
        group_data = group_df.to_dict(orient='records')
        for item in group_data:
            user_data[item['create_time']] = item['count']
        result.append(user_data)

    return {'message': '统计成功!', 'month_detail': result}
