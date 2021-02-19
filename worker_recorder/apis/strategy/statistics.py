# _*_ coding:utf-8 _*_
# @File  : statistics.py
# @Time  : 2021-01-07 11:03
# @Author: zizle

# 投顾策略的统计

# 1. 按月统计每人的投顾策略数量、成功量、成功率、收益、收益率
# 2. 按年统计每人的投顾策略数量、成功量、成功率、收益、收益率

import datetime
import pandas as pd
from fastapi import APIRouter, Query, HTTPException, Depends

from utils.time_handler import get_month_range, get_year_range, get_current_year
from utils.encryption import decipher_user_token
from utils.constants import VARIETY_CN
from .handler import get_strategy, handle_strategy_amount_rate, handle_strategy_amount
from apis.utils import validate_start_date, validate_end_date
from apis.tools import query_work_records, filter_exclude_record

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


@statistics_api.get('/year-total/')  # 按年累计请求者的投顾策略数量(请求者=admin则为所有人的数量)
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
    records = get_strategy(start_timestamp, end_timestamp, 0)
    record_df = pd.DataFrame(records)
    if record_df.empty:
        return {'message': '统计成功!', 'total_count': 0, 'percent': 0, 'month_count': []}
    total_count = record_df.shape[0]
    # 获取查询的用户的数据
    user_record_df = record_df[record_df['author_id'].isin(include_ids)]
    # if 'admin' in access:
    #     detail_count_data = handle_strategy_amount(record_df, 'year')
    #     user_count = total_count
    #     percent = 100 if total_count else 0
    # else:
    #     # 选取用户的投顾策略
    #     user_record_df = record_df[record_df['author_id'] == user_id]
    detail_count_data = handle_strategy_amount(user_record_df, 'year')
    user_count = user_record_df.shape[0]
    percent = round(user_count / total_count * 100, 2) if total_count else 0
    return {'message': '统计成功!', 'total_count': user_count, 'percent': percent, 'month_count': detail_count_data}


""" 2021.02.18 """


def statistics_records(records):  # 对记录集进行统计(数量、标记数)
    record_df = pd.DataFrame(records)
    if record_df.empty:
        return [], []
    # 去除运行中的策略得到要统计的策略
    statistics_df = record_df[record_df['is_running'] == 0]
    if statistics_df.empty:
        return record_df.to_dict(orient='records'), []
    # 1 以作者分组数据统计数量
    record_count_df = statistics_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg(
        {'total_count': 'count'})
    # 2 筛选收益率>0的条目,统计成功率
    success_df = statistics_df[statistics_df['profit'] > 0]
    # 统计各人员的成功数量
    success_count_df = success_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg(
        {'success_count': 'count'})
    # **合并各人员策略数量与成功数量数据框
    result_df = pd.merge(record_count_df, success_count_df, on=['author_id', 'username'], how='left')
    # 3 计算算术平均收益率
    # 计算每条策略的收益率
    statistics_df['profit_rate'] = statistics_df['profit'] / 100000
    # 分组合计每人的收益、收益率加和
    avg_profit_df = statistics_df.groupby(by=['author_id', 'username'])[['profit', 'profit_rate']].sum()
    avg_profit_df = avg_profit_df.reset_index()
    avg_profit_df = avg_profit_df.rename(columns={'profit': 'sum_profit', 'profit_rate': 'sum_profit_rate'})

    # **将数量数据框与平均收益数据框合并
    result_df = pd.merge(result_df, avg_profit_df, on=['author_id', 'username'], how='left')
    # 计算平均收益率
    result_df['avg_profit_rate'] = result_df['sum_profit_rate'] / result_df['total_count']
    # 删除收益率算术平均和的列避免混淆
    # 4. 计算累计收益率（暂时认定就是所有记录的的收益和 / 10万 * 条数 = 每个记录的收益率加总）

    # 5. 计算成功率
    result_df['success_rate'] = result_df['success_count'] / result_df['total_count']

    result_df.fillna(0, inplace=True)

    return record_df.to_dict(orient='records'), result_df.to_dict(orient='records')


def columns_handler(item):  # 处理数据记录字段值
    item['create_time'] = datetime.datetime.fromtimestamp(item['create_time']).strftime('%Y-%m-%d')
    item['contract_name'] = VARIETY_CN.get(item['variety_en'], '') + item['contract']
    return item


@statistics_api.get('/')  # 获取所有再请求id中的投顾策略数据并进行统计
async def statistics_users_strategy(currency: str = Query(...),
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
    query_columns = 't.id,t.*'
    records = query_work_records(ts_start=start_ts, ts_end=end_ts,
                                 table_name='work_strategy', columns=query_columns)
    if not records:
        return {'message': '获取数据成功!', 'records': [], 'statistics': []}
    # 记录以作者过滤和关键词过滤
    records = filter_exclude_record(records, include_ids, include_kw=kw, kw_column='content')
    # 进行统计
    records, statistics = statistics_records(records)
    # 处理字段值
    records = list(map(columns_handler, records))
    return {'message': '获取数据成功!', 'records': records, 'statistics': statistics}

