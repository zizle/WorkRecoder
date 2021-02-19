# _*_ coding:utf-8 _*_
# @File  : statistics.py
# @Time  : 2021-01-12 08:00
# @Author: zizle

# 统计非常态工作记录

import datetime
import pandas as pd
from fastapi import APIRouter, Query, HTTPException, Depends
from utils.time_handler import get_month_range, get_year_range, get_current_year
from utils.encryption import decipher_user_token
from .hanlder import get_abnormal_work, handle_abnormal_amount_score, handle_abnormal_work_amount
from apis.utils import validate_start_date, validate_end_date
from apis.tools import query_work_records, filter_exclude_record
from settings import APP_HOST


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

    records = get_abnormal_work(start_timestamp, end_timestamp, 0)
    record_df = pd.DataFrame(records)
    if record_df.empty:
        return {'message': '统计成功!', 'total_count': 0, 'percent': 0, 'month_count': []}
    total_count = record_df.shape[0]
    # if 'admin' in access:
    #     detail_count_data = handle_abnormal_work_amount(record_df, 'year')
    #     user_count = total_count
    #     percent = 100 if total_count else 0
    # else:
    #     # 选取用户的非常规工作
    #     user_record_df = record_df[record_df['author_id'] == user_id]

    # 获取查询的用户的数据
    user_record_df = record_df[record_df['author_id'].isin(include_ids)]

    detail_count_data = handle_abnormal_work_amount(user_record_df, 'year')
    user_count = user_record_df.shape[0]
    percent = round(user_count / total_count * 100, 2) if total_count else 0
    return {'message': '统计成功!', 'total_count': user_count, 'percent': percent, 'month_count': detail_count_data}


""" 2021.02.03 """


def statistics_records(records):  # 进行记录的统计(以用户分组统计数量、瑞币、收入补贴、评级得分)
    record_df = pd.DataFrame(records)
    # 过滤掉审核没通过的数据条目
    if record_df.empty:
        return [], []
    # 只统计有效的工作记录
    record_df = record_df[record_df['is_examined'] == 1]
    if record_df.empty:
        return [], []
    # 计算各人员的策略数量
    amount_count_df = record_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg(
        {'total_count': 'count'})
    # 统计其他字段
    sum_df = record_df.groupby(by=['author_id'], as_index=False)[['swiss_coin', 'allowance', 'score']].sum()
    # 将数据合并
    sum_df = pd.merge(amount_count_df, sum_df, on=['author_id'], how='left')
    return record_df.to_dict(orient='records'), sum_df.to_dict(orient='records')


def columns_handler(item):
    item['create_time'] = datetime.datetime.fromtimestamp(item['create_time']).strftime('%Y-%m-%d')
    item['annex_url'] = APP_HOST + 'static/' + item['annex_url']
    return item


@statistics_api.get('/')  # 按年统计请求用户id中的非常规工作数量
async def statistics_users_count(currency: str = Query(...),
                                 start_ts: int = Depends(validate_start_date),
                                 end_ts: int = Depends(validate_end_date),
                                 kw: str = Query(None)):
    """
    :param currency: 包含的所有id的字符串
    :param start_ts: 日期开始的时间戳
    :param end_ts: 日期结束的时间戳
    :param kw: 关键词查询
    :return: 响应数据
    """
    # currency: 要查询的用户ids字符串以`,`分割
    include_ids = list(map(int, currency.split(',')))
    # 进行数据获取
    query_columns = 't.id,t.create_time,t.title,t.task_type,t.sponsor,t.applicant,t.phone,t.swiss_coin,t.allowance,' \
                    't.partner,t.note,t.score,t.annex,t.annex_url,t.is_examined'
    records = query_work_records(ts_start=start_ts, ts_end=end_ts,
                                 table_name='work_abnormal', columns=query_columns)
    if not records:
        return {'message': '获取数据成功!', 'records': [], 'statistics': []}
    # 记录以作者过滤和关键词过滤
    records = filter_exclude_record(records, include_ids, include_kw=kw, kw_column='title')
    # 进行统计
    records, statistics = statistics_records(records)
    # 处理字段值
    records = list(map(columns_handler, records))
    return {'message': '获取数据成功!', 'records': records, 'statistics': statistics}
