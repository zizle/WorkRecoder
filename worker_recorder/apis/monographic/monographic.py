# _*_ coding:utf-8 _*_
# @File  : monographic.py
# @Time  : 2021-01-18 13:44
# @Author: zizle

# 专题研究的API
# 1. 获取个人的2020年所有专题研究记录

import datetime
from fastapi import APIRouter, Query, HTTPException
from apis.tools import validate_operate_user
from db import DBWorker
from settings import APP_HOST

monographic_api = APIRouter()


def handle_monographic_item(item):
    item['create_time'] = datetime.datetime.fromtimestamp(item['create_time']).strftime('%Y-%m-%d')
    item['join_time'] = datetime.datetime.fromtimestamp(item['join_time']).strftime('%Y-%m-%d %H:%M:%S')
    item['update_time'] = datetime.datetime.fromtimestamp(item['update_time']).strftime('%Y-%m-%d %H:%M:%S')
    item['annex_url'] = APP_HOST + 'static/' + item['annex_url']
    return item


@monographic_api.get('/')   # 获取个人的专题研究记录
async def get_monographic(user_token: str = Query(...)):
    user_id, is_audit = validate_operate_user(user_token, 'monographic')
    if not user_id:
        raise HTTPException(status_code=401, detail='登录已过期,请重新登录!')
    # 查询记录
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT monotb.*,usertb.username FROM work_monographic AS monotb "
            "INNER JOIN user_user AS usertb ON monotb.author_id=usertb.id "
            "WHERE IF(1=%s,TRUE,monotb.author_id=%s) ORDER BY monotb.create_time;",
            (is_audit, user_id)
        )
        articles = cursor.fetchall()
    articles = list(map(handle_monographic_item, articles))
    return {"message": '查询专题研究成功!', 'articles': articles}



