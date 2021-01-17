# _*_ coding:utf-8 _*_
# @File  : hanlder.py
# @Time  : 2021-01-12 08:01
# @Author: zizle

import datetime
import pandas as pd
from db import DBWorker


def get_hot_article(start_timestamp: int, end_timestamp: int, author_id: int):
    # 查询数据
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT artb.*,usertb.id AS user_id,usertb.username "
            "FROM work_article AS artb "
            "INNER JOIN user_user AS usertb ON artb.author_id=usertb.id "
            "WHERE artb.create_time>=%s AND artb.create_time<%s AND IF(0=%s,TRUE,artb.author_id=%s);",
            (start_timestamp, end_timestamp, author_id, author_id)
        )
        articles = cursor.fetchall()
    return articles


def handle_article_amount_score(article_df):
    if article_df.empty:
        return []
    # 1 计算各人员的文章数量和得分
    # 计算各人员的策略数量
    amount_count_df = article_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg(
        {'total_count': 'count'})
    # 计算得分
    score_df = article_df.groupby(['author_id', 'username'], as_index=False)['score'].agg(
        {'sum_score': 'sum'})
    # 合并
    result_df = pd.merge(amount_count_df, score_df, on=['author_id', 'username'], how='left')

    return result_df.to_dict(orient='records')


# 将投资方案按月统计出数量
def handle_article_amount(article_df, s_type):
    if article_df.empty:
        return []
    if s_type == 'month':
        timestamp_format = '%Y-%m-%d'
    elif s_type == 'year':
        timestamp_format = '%Y-%m'
    else:
        return []
    article_df['create_time'] = article_df['create_time'].apply(
        lambda x: datetime.datetime.fromtimestamp(x).strftime(timestamp_format))
    # 以人员日期格式进行分组统计
    author_date_count_df = article_df.groupby(['author_id', 'username', 'create_time'], as_index=False)[
        'author_id'].agg({'count': 'count'})
    author_date_count_df['author_id'] = author_date_count_df['author_id'].astype(int)
    author_date_count_df['count'] = author_date_count_df['count'].astype(int)
    # 再次根据作者分组
    result = []
    for name, group in author_date_count_df.groupby(['author_id', 'username']):
        user_data = {'author_id': int(name[0]), 'username': str(name[1])}
        group_df = group.set_index('create_time').reset_index()  # 得到日期对应的作者的数量
        group_data = group_df.to_dict(orient='records')
        each_total = 0
        for item in group_data:
            each_total += item['count']
            user_data[item['create_time']] = item['count']
        user_data['year_total'] = each_total
        result.append(user_data)
    return result
