# _*_ coding:utf-8 _*_
# @File  : tools.py
# @Time  : 2021-01-07 08:48
# @Author: zizle

import datetime
import pandas as pd
from fastapi import HTTPException
from utils.encryption import decipher_user_token
from db import DBWorker


# 验证用户
def validate_operate_user(user_token, audit=None):
    user_id, access = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期!请重新登录。')
    # 判断是否为管理页获取
    is_audit = 0
    if audit:
        if 'admin' in access or audit in access:
            is_audit = 1
    return user_id, is_audit


# 处理时间区域
def validate_date_range(start_date, end_date):
    try:
        start_timestamp = int(datetime.datetime.strptime(start_date, '%Y-%m-%d').timestamp())
        end_timestamp = int(datetime.datetime.strptime(end_date, '%Y-%m-%d').timestamp())
        if start_timestamp == end_timestamp:
            end_timestamp = int((datetime.datetime.fromtimestamp(end_timestamp) + datetime.timedelta(days=1)).timestamp())
        if start_timestamp > end_timestamp:
            raise ValueError('Error')
    except ValueError:
        raise HTTPException(status_code=400, detail='参数错误!')
    return start_timestamp, end_timestamp


# 过滤数据
def filter_records(
        is_audit, req_staff, keyword, key_column, records, total_records
):
    if is_audit and req_staff:
        records = list(filter(lambda x: x['author_id'] in req_staff, records))
    if total_records:
        total_records = list(filter(lambda x: x['author_id'] in req_staff, total_records))
    if keyword:
        records = list(filter(lambda x: keyword in x[key_column], records))
    if total_records:
        total_records = list(filter(lambda x: keyword in x[key_column], total_records))
    return records, total_records


""" 2021.02.03 """


def query_work_records(ts_start: int, ts_end: int, table_name: str, columns: str):
    """
    查询指定时间戳范围内的指定数据表的数据
    :param ts_start: 日期起始时间戳
    :param ts_end: 日期结束时间戳
    :param table_name: 查询的工作记录表名称
    :param columns: 查询的字段
    :return: records-记录条目list
    """
    query ="SELECT u.username,t.author_id,{} FROM {} AS t " \
           "INNER JOIN user_user AS u ON u.id=t.author_id " \
           "WHERE t.create_time>=%s AND t.create_time<=%s;".format(columns, table_name)
    with DBWorker() as (_, cursor):
        cursor.execute(
            query, (ts_start, ts_end)
        )
        records = cursor.fetchall()
    return records


def filter_exclude_record(records: list, include_ids: list, include_kw: str, kw_column: str):
    """
    过滤掉指定用户外的数据
    :param records: 记录条目
    :param include_ids: 要的作者id列表
    :param include_kw: 包含的关键字
    :param kw_column: 在哪列查找包含的关键词
    :return: 过滤后的数据
    """
    data_frame = pd.DataFrame(records)
    data_frame = data_frame[data_frame['author_id'].isin(include_ids)]
    if include_kw:
        data_frame = data_frame[data_frame[kw_column].str.contains(include_kw, regex=False)]
    return data_frame.to_dict(orient='records')

