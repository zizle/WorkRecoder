# _*_ coding:utf-8 _*_

# 品种的API
# 1. 添加一个品种
# 2. 获取品种列表
import datetime

from fastapi import APIRouter
from db import DBWorker
from utils.constants import VARIETY_GROUPS, EXCHANGES

variety_api = APIRouter()


@variety_api.get('/all/')  # 获取全部的品种,以交易代码排序
async def get_all_variety():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT id,create_time,update_time,variety_name,variety_en,group_id,exchange_id "
            "FROM variety_variety;"
        )
        varieties = cursor.fetchall()

    for v_item in varieties:
        v_item['create_time'] = datetime.datetime.fromtimestamp(v_item['create_time']).strftime('%Y-%m-%d %H:%M:%S')
        v_item['update_time'] = datetime.datetime.fromtimestamp(v_item['update_time']).strftime('%Y-%m-%d %H:%M:%S')
        v_item['group_name'] = VARIETY_GROUPS.get(v_item['group_id'], '未知')
        v_item['exchange_name'] = VARIETY_GROUPS.get(v_item['exchange_id'], '未知')

    return {'message': '获取品种成功!', 'varieties': varieties}




