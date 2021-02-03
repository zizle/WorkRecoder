# _*_ coding:utf-8 _*_
# @File  : utils.py
# @Time  : 2021-02-03 13:41
# @Author: zizle
import datetime
from fastapi import HTTPException, Query


def validate_start_date(start: str = Query(...)):
    try:
        ts = int(datetime.datetime.strptime(start, '%Y%m%d').timestamp())
    except Exception:
        raise HTTPException(status_code=400, detail='start param can not format %Y%m%d.')
    return ts


def validate_end_date(end: str = Query(...)):
    try:
        ts = int(datetime.datetime.strptime(end, '%Y%m%d').timestamp())
    except Exception:
        raise HTTPException(status_code=400, detail='end param can not format %Y%m%d.')
    return ts
