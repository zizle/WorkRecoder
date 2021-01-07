# _*_ coding:utf-8 _*_
# @File  : tools.py
# @Time  : 2021-01-07 08:48
# @Author: zizle

import datetime
from fastapi import HTTPException
from utils.encryption import decipher_user_token


# 验证用户
def validate_operate_user(user_token, audit=None):
    user_id, access = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期!请重新登录。')
    # 判断是否为管理页获取
    is_audit = 0
    if audit:
        if 'admin' not in access and audit not in access:
            raise HTTPException(status_code=403, detail='不能这样操作!')
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
def filter_records(is_audit, req_staff, keyword, records, total_records):
    if is_audit and req_staff:
        records = list(filter(lambda x: x['author_id'] in req_staff, records))
        total_records = list(filter(lambda x: x['author_id'] in req_staff, total_records))
    if keyword:
        records = list(filter(lambda x: keyword in x['content'], records))
        total_records = list(filter(lambda x: keyword in x['content'], total_records))
    return records, total_records
