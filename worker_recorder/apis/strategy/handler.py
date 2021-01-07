# _*_ coding:utf-8 _*_
# @File  : handler.py
# @Time  : 2021-01-07 11:19
# @Author: zizle

import pandas as pd
from db import DBWorker


def get_strategy(start_timestamp: int, end_timestamp: int, author_id: int):
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT * "
            "FROM work_strategy AS stb "
            "INNER JOIN user_user AS usertb ON stb.author_id=usertb.id "
            "WHERE stb.create_time>=%s AND stb.create_time<%s AND IF(0=%s,TRUE,stb.author_id=%s);",
            (start_timestamp, end_timestamp, author_id, author_id)
        )
        strategies = cursor.fetchall()
    return strategies


# 按作者处理统计投顾策略数量和成功率排名
def handle_strategy_amount_rate(strategy_df):
    if strategy_df.empty:
        return []

    # 分组计算的每人的收益总和
    sum_profit_df = strategy_df.groupby(by=['author_id', 'username'])['profit'].sum()
    sum_profit_df = sum_profit_df.to_frame()
    sum_profit_df = sum_profit_df.reset_index()
    sum_profit_df = sum_profit_df.rename(columns={'profit': 'sum_profit'})

    # 计算各人员的数量
    amount_count_df = strategy_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg(
        {'total_count': 'count'})

    # 将数量数据框与累计收益数据框合并
    result_df = pd.merge(sum_profit_df, amount_count_df, on=['author_id', 'username'], how='inner')

    # 筛选收益率>0的条目
    success_df = strategy_df[strategy_df['profit'] > 0]
    # 统计各人员的成功数量
    success_count_df = success_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg(
        {'success_count': 'count'})

    # 将成功数量与结果数据框合并
    result_df = pd.merge(result_df, success_count_df, on=['author_id', 'username'], how='inner')

    # 计算成功率
    result_df['success_rate'] = result_df['success_count'] / result_df['total_count']
    # 计算累计总收益率
    result_df['sum_profit_rate'] = result_df['sum_profit'] / (100000 * result_df['total_count'])

    return result_df.to_dict(orient='records')
