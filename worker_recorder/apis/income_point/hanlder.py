# _*_ coding:utf-8 _*_
# @File  : hanlder.py
# @Time  : 2021-01-13 15:33
# @Author: zizle

import datetime
import pandas as pd
from db import DBWorker

# 获取所有客户
def get_customers():
    with DBWorker() as (_, cursor):
        # 查询所有客户
        cursor.execute(
            "SELECT csttb.id AS customer_id,csttb.create_time AS customer_create,csttb.author_id,"
            "csttb.customer_name,usetb.username "
            "FROM work_customer AS csttb "
            "INNER JOIN user_user AS usetb ON csttb.author_id=usetb.id;"
        )
        customers = cursor.fetchall()
    return customers


# 获取客户的最新权益记录
def get_customer_revenue():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT t.create_time AS revenue_create,t.customer_id,t.remain,t.interest,t.crights "
            "FROM ("
            "SELECT customer_id,max(create_time) as create_time FROM work_customer_index GROUP BY customer_id"
            ") AS a "
            "INNER JOIN work_customer_index AS t "
            "ON t.customer_id=a.customer_id AND t.create_time=a.create_time;"
        )
        customer_revenue = cursor.fetchall()
    return customer_revenue


def handle_customer_amount_revenue(customer_df, revenue_df):
    if customer_df.empty:
        return []
    # 转日期格式
    customer_df['customer_create'] = customer_df['customer_create'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d'))
    revenue_df['revenue_create'] = revenue_df['revenue_create'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d'))
    # 以customer_id为键横向合并数据框
    result_df = pd.merge(customer_df, revenue_df, on=['customer_id'], how='left')
    # 统计数量
    # 1 计算各人员的客户数量
    amount_count_df = result_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg(
        {'total_count': 'count'})
    # print(amount_count_df)
    # 2 计算各人员的客户所有权益和
    sum_revenue_df = result_df.groupby(by=['author_id', 'username'], as_index=False)[
        ['remain', 'interest', 'crights']].sum()
    # print(sum_revenue_df)
    # 合并数量和权益和的数据框
    result_df = pd.merge(amount_count_df, sum_revenue_df, on=['author_id', 'username'], how='inner')
    return result_df.to_dict(orient='records')








