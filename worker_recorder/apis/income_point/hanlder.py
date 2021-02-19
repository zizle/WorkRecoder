# _*_ coding:utf-8 _*_
# @File  : hanlder.py
# @Time  : 2021-01-13 15:33
# @Author: zizle

import datetime
import pandas as pd
from db import DBWorker


# 获取指定用户的所有客户和权益记录信息(管理员获取所有)
def get_customers_and_revenues(start_timestamp: int, end_timestamp: int, author_id: int):
    with DBWorker() as (_, cursor):
        # 查询所有客户
        cursor.execute(
            "SELECT csttb.id AS customer_id,csttb.create_time AS customer_create,csttb.author_id,"
            "csttb.customer_name,usetb.username "
            "FROM work_customer AS csttb "
            "INNER JOIN user_user AS usetb ON csttb.author_id=usetb.id "
            "WHERE IF(0=%s,TRUE,csttb.author_id=%s);",
            (author_id, author_id)
        )
        customers = cursor.fetchall()
        # 连表查询所有权益记录
        cursor.execute(
            "SELECT * "
            "FROM work_customer_index AS revetb "
            "INNER JOIN work_customer AS csttb ON revetb.customer_id=csttb.id "
            "WHERE revetb.create_time>=%s AND revetb.create_time<%s AND IF(0=%s,TRUE,csttb.author_id=%s);",
            (start_timestamp, end_timestamp, author_id, author_id)
        )
        revenues = cursor.fetchall()
    return customers, revenues


# 获取指定日期中的客户权益记录信息(管理员获取所有)
def get_customer_revenue(start_timestamp: int, end_timestamp: int, author_id: int):
    with DBWorker() as (_, cursor):
        # 获取最新的权益记录条目
        # cursor.execute(
        #     "SELECT t.create_time AS revenue_create,t.customer_id,t.remain,t.interest,t.crights "
        #     "FROM ("
        #     "SELECT customer_id,max(create_time) as create_time FROM work_customer_index GROUP BY customer_id"
        #     ") AS a "
        #     "INNER JOIN work_customer_index AS t "
        #     "ON t.customer_id=a.customer_id AND t.create_time=a.create_time;"
        # )
        # 获取所有指定的权益记录信息
        customer_revenue = cursor.fetchall()
    return customer_revenue

# 处理获取客户及其权益,收入(留存 + 利息)
def handle_customer_amount_revenue(customer_df, revenue_df):
    if customer_df.empty:
        return []
    if revenue_df.empty:
        row_count = customer_df.shape[0]
        # 直接添加每个客户的留存，利息，权益都为空
        customer_df['sum_remain'] = [0 for _ in range(row_count)]
        customer_df['sum_interest'] = [0 for _ in range(row_count)]
        customer_df['sum_income'] = [0 for _ in range(row_count)]
        customer_df['crights'] = [0 for _ in range(row_count)]
        customer_df['create_time'] = ['' for _ in range(row_count)]
        result_df = customer_df
    else:
        # 处理留存和利息权益的问题：留存和利息以客户为主累计加和，权益取create_time最大的一条
        sum_revenue_df = revenue_df.groupby(by=['customer_id'], as_index=False)[['remain', 'interest']].sum()
        sum_revenue_df = sum_revenue_df.reset_index()
        sum_revenue_df = sum_revenue_df.rename(columns={'remain': 'sum_remain', 'interest': 'sum_interest'})  # 这是留存和利息的加和数据
        sum_revenue_df['sum_income'] = sum_revenue_df['sum_remain'] + sum_revenue_df['sum_interest']
        # 排序后分组取第一条
        rights_df = revenue_df.sort_values('create_time', ascending=False).groupby(by=['customer_id'], as_index=False).first()
        rights_df = rights_df[['create_time', 'customer_id', 'author_id', 'crights']]  # 取需要的列
        # 合并留存，利息和权益数据框
        result_revenue_df = pd.merge(sum_revenue_df, rights_df, on=['customer_id'], how='left')
        # 转create_time格式
        result_revenue_df['create_time'] = result_revenue_df['create_time'].apply(
            lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d'))
        # 再与客户数据合并
        result_df = pd.merge(customer_df, result_revenue_df, on=['customer_id', 'author_id'], how='left')
        # 填0
        result_df.fillna(0, inplace=True)
    # 最后转客户的创建日期格式
    result_df['customer_create'] = result_df['customer_create'].apply(
        lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d'))
    # 1 计算各人员的客户数量
    amount_count_df = result_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg(
        {'total_count': 'count'})
    # 2 计算各人员的客户所有权益和
    sum_revenue_df = result_df.groupby(by=['author_id', 'username'], as_index=False)[
        ['sum_remain', 'sum_interest', 'sum_income', 'crights']].sum()
    # 合并数量和权益和的数据框
    result_data_df = pd.merge(amount_count_df, sum_revenue_df, on=['author_id', 'username'], how='inner')
    return result_data_df.to_dict(orient='records')
