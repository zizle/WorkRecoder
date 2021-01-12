# _*_ coding:utf-8 _*_
# @File  : hanlder.py
# @Time  : 2021-01-12 08:01
# @Author: zizle

import datetime
import pandas as pd
from db import DBWorker


def get_investment(start_timestamp: int, end_timestamp: int, author_id: int):
    # 查询数据
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT ivtb.*,usertb.id AS user_id,usertb.username "
            "FROM work_investment AS ivtb "
            "INNER JOIN user_user AS usertb ON ivtb.author_id=usertb.id "
            "WHERE ivtb.create_time>=%s AND ivtb.create_time<%s AND IF(0=%s,TRUE,ivtb.author_id=%s);",
            (start_timestamp, end_timestamp, author_id, author_id)
        )
        investments = cursor.fetchall()
    return investments


def handle_investment_amount_rate(investment_df, ):
    if investment_df.empty:
        return []
    # 只统计已结束的方案
    investment_df = investment_df[investment_df['is_running'] == 0]
    if investment_df.empty:
        return []
    # 计算每条方案收益率
    investment_df['profit_rate'] = investment_df['profit'] / 1000000

    # 1 计算各人员的策略数量
    amount_count_df = investment_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg(
        {'total_count': 'count'})

    # 2 计算各人员成功的方案数量,也就是盈利的方案数量
    # 选取收益>0的条目
    success_df = investment_df[investment_df['profit'] > 0]
    # 统计各人员的成功数量
    success_count_df = success_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg(
        {'success_count': 'count'})

    # ** 合并各人员的方案数量与成功的数量为新的数据框
    result_df = pd.merge(amount_count_df, success_count_df, on=['author_id', 'username'], how='left')

    # 3 计算算术平均收益率和得分
    # 分组合计每人的收益、收益率、得分加和
    # 转数据类型(score原为int,而其他为decimal会丢失)
    investment_df[['profit', 'score', 'profit_rate']] = investment_df[['profit', 'score', 'profit_rate']].astype(float)
    avg_profit_df = investment_df.groupby(by=['author_id', 'username'], as_index=False)[['profit', 'score', 'profit_rate']].sum()
    avg_profit_df = avg_profit_df.reset_index()
    avg_profit_df = avg_profit_df.rename(
        columns={'profit': 'sum_profit', 'profit_rate': 'sum_profit_rate', 'score': 'sum_score'})
    # **将数量数据框与平均收益数据框合并
    result_df = pd.merge(result_df, avg_profit_df, on=['author_id', 'username'], how='left')
    # 计算平均收益率
    result_df['avg_profit_rate'] = result_df['sum_profit_rate'] / result_df['total_count']

    # 4. 计算累计收益率（暂时认定就是所有记录的的收益和 / 100万 * 条数 = 每个记录的收益率加总）

    # 5. 计算成功率
    result_df['success_rate'] = result_df['success_count'] / result_df['total_count']

    result_df.fillna(0, inplace=True)

    return result_df.to_dict(orient='records')


# 将投资方案按月统计出数量
def handle_investment_amount(investment_df, s_type):
    if investment_df.empty:
        return []
    if s_type == 'month':
        timestamp_format = '%Y-%m-%d'
    elif s_type == 'year':
        timestamp_format = '%Y-%m'
    else:
        return []
    investment_df['create_time'] = investment_df['create_time'].apply(
        lambda x: datetime.datetime.fromtimestamp(x).strftime(timestamp_format))
    # 以人员日期格式进行分组统计
    author_date_count_df = investment_df.groupby(['author_id', 'username', 'create_time'], as_index=False)[
        'author_id'].agg({'count': 'count'})
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
    return result
