# _*_ coding:utf-8 _*_
# @File  : time_handler.py
# @Time  : 2021-01-05 15:18
# @Author: zizle
import datetime


def get_year_range(query_date: str):
    try:
        query_date = datetime.datetime.strptime(query_date, '%Y-01-01')
    except ValueError:
        return 0, 0
    year = query_date.year
    end_date = datetime.datetime.strptime('{}-01-01'.format(year + 1), '%Y-01-01')
    start_timestamp = int(query_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    return start_timestamp, end_timestamp


def get_month_range(query_date: str):
    try:
        query_date = datetime.datetime.strptime(query_date, '%Y-%m-01')
    except ValueError:
        return 0, 0
    year = query_date.year
    month = query_date.month
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    end_date = datetime.datetime.strptime('{}-{}-01'.format(year, month), '%Y-%m-01')
    start_timestamp = int(query_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    return start_timestamp, end_timestamp


def get_current_year(swap_month=1, swap_day=28):
    # 获取日期范围(swap_month月swap_day日(含)之后就显示新一年的)
    today = datetime.datetime.today()
    year = today.year
    month = today.month
    day = today.day
    if month == swap_month and day < swap_day:
        # 显示去年的数据
        current_year = '{}-01-01'.format(year - 1)
    else:
        current_year = '{}-01-01'.format(year)
    return current_year