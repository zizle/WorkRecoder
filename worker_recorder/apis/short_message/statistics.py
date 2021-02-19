# _*_ coding:utf-8 _*_
# @File  : statistics.py
# @Time  : 2021-01-04 14:50
# @Author: zizle

# 短讯通统计API
# 1. 按月统计每人的短讯通数量和被标记数量
# 2. 按月统计每人每天的短讯通数量
# 3. 按年统计每人的短讯通数量和被标记数量
# 4. 按年统计每人每个月的短讯通数量
# 5. 按年累计请求者的短讯通数量(请求者=admin则为所有人的数量),并返回请求者(admin则是所有用户)分月的详情数据

import datetime
import pandas as pd
from fastapi import APIRouter, Query, HTTPException, Depends

from utils.encryption import decipher_user_token
from utils.time_handler import get_year_range, get_month_range, get_current_year
from utils.constants import MSG_AUDIT_MIND
from .handler import get_messages, handle_detail_amount, handle_amount_audit_rank
from apis.utils import validate_start_date, validate_end_date
from apis.tools import query_work_records, filter_exclude_record


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


@statistics_api.get('/year-total/')  # 按年累计请求者的短讯通数量(请求者=admin则为所有人的数量),并返回请求者(admin则是所有用户)分月的详情数据
async def get_user_year_total(user_token: str = Query(...),
                              currency: str = Query(...)):
    # 解析出用户
    user_id, access = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期,请重新登录!')
    include_ids = list(map(int, currency.split(',')))
    # 获取日期范围(1月28日(含)之后就显示新一年的)
    current_year = get_current_year()
    start_timestamp, end_timestamp = get_year_range(current_year)
    if start_timestamp == 0:
        raise HTTPException(status_code=400, detail='参数`query_date`错误:can not format `%Y-01-01`.')
    message = get_messages(start_timestamp, end_timestamp, 0)
    message_df = pd.DataFrame(message)
    if message_df.empty:
        return {'message': '统计成功!', 'total_count': 0, 'percent': 0, 'month_count': []}
    total_count = message_df.shape[0]
    # 获取查询的用户的数据
    user_message_df = message_df[message_df['author_id'].isin(include_ids)]
    # if 'admin' in access:
    #     detail_count_data = handle_detail_amount(message_df, 'year')
    #     user_count = total_count
    #     percent = 100 if total_count else 0
    # else:
    #     # 选取用户的短讯通
    #     user_message_df = message_df[message_df['author_id'] == user_id]
    #     # 选取查询的用户短讯通
    #     detail_count_data = handle_detail_amount(user_message_df, 'year')
    #     user_count = user_message_df.shape[0]
    #     percent = round(user_count / total_count * 100, 2) if total_count else 0
    # 选取查询的用户短讯通
    detail_count_data = handle_detail_amount(user_message_df, 'year')
    user_count = user_message_df.shape[0]
    percent = round(user_count / total_count * 100, 2) if total_count else 0
    return {'message': '统计成功!', 'total_count': user_count, 'percent': percent, 'month_count': detail_count_data}


""" 2021.02.04 """


def statistics_records(records):  # 对记录集进行统计(数量、标记数)
    record_df = pd.DataFrame(records)
    if record_df.empty:
        return [], []
    # 以作者分组数据统计数量
    record_count_df = record_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg(
        {'total_count': 'count'})
    # 对标记数量进行统计
    message_audit_df = record_df[~(record_df['audit_mind'] == 0)]  # 筛选出audit_mind != 0的
    # 对此进行分组统计
    audit_count_df = message_audit_df.groupby(['author_id'], as_index=False)['author_id'].agg(
        {'audit_count': 'count'})
    # 合并两个数据框,并补0
    result_df = pd.merge(record_count_df, audit_count_df, on=['author_id'], how='left')
    result_df.fillna(0, inplace=True)
    return record_df.to_dict(orient='records'), result_df.to_dict(orient='records')


def columns_handler(item):  # 处理数据记录字段值
    item['create_time'] = datetime.datetime.fromtimestamp(item['create_time']).strftime('%Y-%m-%d')
    item['audit_description'] = '标记意见：{}'.format(MSG_AUDIT_MIND.get(item['audit_mind'], '无'))
    return item


@statistics_api.get('/')  # 获取所有在请求id中的短讯通数据并统计
async def statistics_users_short_message(currency: str = Query(...),
                                         start_ts: int = Depends(validate_start_date),
                                         end_ts: int = Depends(validate_end_date),
                                         kw: str = Query(None)):
    """
    根据参数获取到记录并进行需求统计
    :param currency: 要请求的用户id字符串
    :param start_ts: 日期开始时间戳
    :param end_ts: 日期结束的时间戳
    :param kw: 关键词查询
    :return: 响应数据
    """
    include_ids = list(map(int, currency.split(',')))
    # 进行数据获取
    query_columns = 't.id,t.create_time,t.content,t.msg_type,t.effects,t.note,t.audit_mind'
    records = query_work_records(ts_start=start_ts, ts_end=end_ts,
                                 table_name='work_short_message', columns=query_columns)
    if not records:
        return {'message': '获取数据成功!', 'records': [], 'statistics': []}
    # 记录以作者过滤和关键词过滤
    records = filter_exclude_record(records, include_ids, include_kw=kw, kw_column='content')
    # # 进行统计
    records, statistics = statistics_records(records)
    # # 处理字段值
    records = list(map(columns_handler, records))
    return {'message': '获取数据成功!', 'records': records, 'statistics': statistics}
