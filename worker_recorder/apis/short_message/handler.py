# _*_ coding:utf-8 _*_
# @File  : handler.py
# @Time  : 2021-01-05 15:38
# @Author: zizle

import datetime
from db import DBWorker


def get_messages(start_timestamp: int, end_timestamp: int, author_id: int):
    # 查询数据
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT msgtb.id,msgtb.create_time,msgtb.author_id,usertb.id as user_id,usertb.username,msgtb.audit_mind "
            "FROM work_short_message AS msgtb "
            "INNER JOIN user_user AS usertb ON msgtb.author_id=usertb.id "
            "WHERE msgtb.create_time>=%s AND msgtb.create_time<%s AND IF(0=%s,TRUE,msgtb.author_id=%s);",
            (start_timestamp, end_timestamp, author_id, author_id)
        )
        messages = cursor.fetchall()
    return messages


# 按作者计数短讯通数量和被标记的数量
def handle_amount_audit_rank(message_df):
    if message_df.empty:
        return [], []
    # 以作者分组统计
    author_count_df = message_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg({'count': 'count'})
    author_count_df['rank'] = author_count_df['count'].rank(method='dense', ascending=False).astype(int)
    amount_rank = author_count_df.to_dict(orient='records')
    # 以作者分组,audit_mind!=0标记统计
    # 筛选出audit_mind != 0的
    message_audit_df = message_df[~(message_df['audit_mind'] == 0)]
    # 对此进行分组统计
    audit_mind_count_df = message_audit_df.groupby(['author_id', 'username'], as_index=False)['author_id'].agg(
        {'count': 'count'})
    audit_mind_count_df['rank'] = audit_mind_count_df['count'].rank(method='dense', ascending=False).astype(int)
    quality_rank = audit_mind_count_df.to_dict(orient='records')
    return amount_rank, quality_rank


# 处理日或月的数量详情表
def handle_detail_amount(message_df, detail):
    if message_df.empty:
        return []
    # 转化日期
    if detail == 'month':
        timestamp_format = '%Y-%m-%d'
    elif detail == 'year':
        timestamp_format = '%Y-%m'
    else:
        return []
    message_df['create_time'] = message_df['create_time'].apply(
        lambda x: datetime.datetime.fromtimestamp(x).strftime(timestamp_format))
    # 以人员日期格式进行分组统计
    author_date_count_df = message_df.groupby(['author_id', 'username', 'create_time'], as_index=False)['author_id'].agg({'count': 'count'})
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
