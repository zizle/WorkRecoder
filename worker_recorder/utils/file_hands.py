# _*_ coding:utf-8 _*_
# @File  : file_hands.py
# @Time  : 2020-12-29 14:17
# @Author: zizle

# 处理文件的方法


import numpy as np
import datetime


# 转换日期列
def date_column_converter(source_datetime):
    if isinstance(source_datetime, datetime.datetime):
        return int(source_datetime.timestamp())
    else:
        return np.nan
