# _*_ coding:utf-8 _*_
# @File  : statistics.py
# @Time  : 2021-01-05 15:00
# @Author: zizle

# 所有模块的数量

import datetime
import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from utils.encryption import decipher_user_token
from utils.time_handler import get_year_range
from apis.short_message.handler import get_messages, handle_detail_amount
from apis.strategy.handler import get_strategy, handle_strategy_amount
from apis.investment.hanlder import get_investment, handle_investment_amount
from apis.abnormal.hanlder import get_abnormal_work, handle_abnormal_work_amount
from apis.hot_article.hanlder import get_hot_article, handle_article_amount
from apis.onduty_message.hanlder import get_onduty_message, handle_onduty_message_point_amount


statistics_router = APIRouter()


def get_message_statistics_data(start_timestamp, end_timestamp, user_id):
    # 获取短讯通的数据
    short_messages = get_messages(start_timestamp, end_timestamp, user_id)
    # 按月分组处理数据
    statistics_messages = handle_detail_amount(pd.DataFrame(short_messages), 'year')
    # print(statistics_messages)
    msg_statistics_df = pd.DataFrame(statistics_messages)  # 转dataFrame计算每列的和
    if msg_statistics_df.empty:
        short_message_data = {
            'series_name': '短讯通',
            'area_color': '#2d8cf0',
            'series_data': []
        }
    else:
        # 删除author_id 和 username列
        del msg_statistics_df['author_id']
        del msg_statistics_df['username']
        # 求和
        msg_statistics_df.loc['col_sum'] = msg_statistics_df.sum()
        msg_statistics_df.sort_index(axis=1, inplace=True)
        # 得到短讯通的数据
        short_message_amount = msg_statistics_df.tail(1).to_dict(orient='records')[0]
        short_message_data = {
            'series_name': '短讯通',
            'area_color': '#2d8cf0',
            'series_data': [{'month': k, 'count': v} for k, v in short_message_amount.items()]
        }

    return short_message_data


def get_strategy_statistics_data(start_timestamp, end_timestamp, user_id):
    # 统计投顾策略的数据
    strategies = get_strategy(start_timestamp, end_timestamp, user_id)
    # 按月分组处理数据
    statistics_strategy = handle_strategy_amount(pd.DataFrame(strategies), 'year')
    # print(statistics_messages)
    stra_statistics_df = pd.DataFrame(statistics_strategy)  # 转dataFrame计算每列的和
    if stra_statistics_df.empty:
        strategy_data = {
            'series_name': '投顾策略',
            'area_color': '#19be6b',
            'series_data': []
        }
    else:
        # 删除author_id 和 username列
        del stra_statistics_df['author_id']
        del stra_statistics_df['username']
        # 求和
        stra_statistics_df.loc['col_sum'] = stra_statistics_df.sum()
        stra_statistics_df.sort_index(axis=1, inplace=True)
        # 得到短讯通的数据
        strategy_amount = stra_statistics_df.tail(1).to_dict(orient='records')[0]
        strategy_data = {
            'series_name': '投顾策略',
            'area_color': '#19be6b',
            'series_data': [{'month': k, 'count': v} for k, v in strategy_amount.items()]
        }
    return strategy_data


def get_investment_statistics_data(start_timestamp, end_timestamp, user_id):
    # 统计投资方案的数据
    investments = get_investment(start_timestamp, end_timestamp, user_id)
    # 按月分组处理数据
    statistics_investment = handle_investment_amount(pd.DataFrame(investments), 'year')
    # print(statistics_messages)
    ivst_statistics_df = pd.DataFrame(statistics_investment)  # 转dataFrame计算每列的和
    if ivst_statistics_df.empty:
        ivst_data = {
            'series_name': '投资方案',
            'area_color': '#ff9900',
            'series_data': []
        }
    else:
        # 删除author_id 和 username列
        del ivst_statistics_df['author_id']
        del ivst_statistics_df['username']
        # 求和
        ivst_statistics_df.loc['col_sum'] = ivst_statistics_df.sum()
        ivst_statistics_df.sort_index(axis=1, inplace=True)
        # 得到短讯通的数据
        ivst_amount = ivst_statistics_df.tail(1).to_dict(orient='records')[0]
        ivst_data = {
            'series_name': '投资方案',
            'area_color': '#ff9900',
            'series_data': [{'month': k, 'count': v} for k, v in ivst_amount.items()]
        }
    return ivst_data


def get_abnormal_statistics_data(start_timestamp, end_timestamp, user_id):
    # 统计非常规工作的数据
    abnormal_works = get_abnormal_work(start_timestamp, end_timestamp, user_id)
    # 按月分组处理数据
    abnormal_works = handle_abnormal_work_amount(pd.DataFrame(abnormal_works), 'year')
    # print(statistics_messages)
    abwk_statistics_df = pd.DataFrame(abnormal_works)  # 转dataFrame计算每列的和
    if abwk_statistics_df.empty:
        abwk_data = {
            'series_name': '非常态工作',
            'area_color': '#ed3f14',
            'series_data': []
        }
    else:
        # 删除author_id 和 username列
        del abwk_statistics_df['author_id']
        del abwk_statistics_df['username']
        # 求和
        abwk_statistics_df.loc['col_sum'] = abwk_statistics_df.sum()
        # 得到短讯通的数据
        abwk_statistics_df.sort_index(axis=1, inplace=True)
        abwk_amount = abwk_statistics_df.tail(1).to_dict(orient='records')[0]
        abwk_data = {
            'series_name': '非常态工作',
            'area_color': '#ed3f14',
            'series_data': [{'month': k, 'count': v} for k, v in abwk_amount.items()]
        }
    return abwk_data


def get_article_statistics_data(start_timestamp, end_timestamp, user_id):
    # 统计热点文章
    hot_articles = get_hot_article(start_timestamp, end_timestamp, user_id)
    # 按月分组处理数据
    hot_articles = handle_article_amount(pd.DataFrame(hot_articles), 'year')
    article_statistics_df = pd.DataFrame(hot_articles)  # 转dataFrame计算每列的和
    if article_statistics_df.empty:
        article_data = {
            'series_name': '热点文章',
            'area_color': '#9a66e4',
            'series_data': []
        }
    else:
        # 删除author_id 和 username列
        del article_statistics_df['author_id']
        del article_statistics_df['username']
        # 求和
        article_statistics_df.loc['col_sum'] = article_statistics_df.sum()
        # 得到短讯通的数据
        article_statistics_df.sort_index(axis=1, inplace=True)
        article_amount = article_statistics_df.tail(1).to_dict(orient='records')[0]
        article_data = {
            'series_name': '热点文章',
            'area_color': '#9a66e4',
            'series_data': [{'month': k, 'count': v} for k, v in article_amount.items()]
        }
    return article_data


def get_onduty_message_statistics_data(start_timestamp, end_timestamp, user_id):
    # 统计值班信息
    records = get_onduty_message(start_timestamp, end_timestamp, user_id)
    # 按月分组处理数据
    records = handle_onduty_message_point_amount(pd.DataFrame(records), 'year')
    record_statistics_df = pd.DataFrame(records)  # 转dataFrame计算每列的和
    if record_statistics_df.empty:
        record_data = {
            'series_name': '值班信息',
            'area_color': '#bf9000',
            'series_data': []
        }
    else:
        # 删除author_id 和 username列
        del record_statistics_df['author_id']
        del record_statistics_df['username']
        # 求和
        record_statistics_df.loc['col_sum'] = record_statistics_df.sum()
        # 得到值班信息
        record_statistics_df.sort_index(axis=1, inplace=True)
        article_amount = record_statistics_df.tail(1).to_dict(orient='records')[0]
        record_data = {
            'series_name': '值班信息',
            'area_color': '#bf9000',
            'series_data': [{'month': k, 'count': v} for k, v in article_amount.items()]
        }
    return record_data


@statistics_router.get('/month-count/')
async def user_all_amount(user_token: str = Query(...)):
    user_id, access = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录已过期,请重新登录!')
    if 'admin' in access:
        user_id = 0
    # 获取起始日期
    # current_year = datetime.datetime.today().strftime('%Y-01-01')
    current_year = '2020-01-01'
    start_timestamp, end_timestamp = get_year_range(current_year)

    short_message_data = get_message_statistics_data(start_timestamp, end_timestamp, user_id)
    strategy_data = get_strategy_statistics_data(start_timestamp, end_timestamp, user_id)
    investment_data = get_investment_statistics_data(start_timestamp, end_timestamp, user_id)
    abnormal_work_data = get_abnormal_statistics_data(start_timestamp, end_timestamp, user_id)
    hot_article_data = get_article_statistics_data(start_timestamp, end_timestamp, user_id)
    onduty_message_data = get_onduty_message_statistics_data(start_timestamp, end_timestamp, user_id)

    data = [short_message_data, strategy_data, investment_data, abnormal_work_data, hot_article_data,
            onduty_message_data]

    # for d in data:
    #     print(d)

    return {'message': '统计成功!', 'data': data}


