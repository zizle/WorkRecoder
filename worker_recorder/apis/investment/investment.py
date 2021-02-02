# _*_ coding:utf-8 _*_
# @File  : investment.py
# @Time  : 2021-01-11 08:47
# @Author: zizle

# 投资方案API
# 1. 用户添加一条投资方案(可能含附件)

import os
import datetime
from fastapi import APIRouter, Form, UploadFile, Depends, Body, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from apis.tools import validate_operate_user, validate_date_range, filter_records
from utils.file_hands import get_file_paths
from utils.constants import VARIETY_CN
from db import DBWorker
from settings import APP_HOST, STATICS_STORAGE
from .validate_models import (InvestmentAddBodyItem, get_investment_content_item, QueryInvestmentItem,
                              InvestmentModifyBodyItem, get_investment_modify_item)


investment_api = APIRouter()


def handle_investment_item(item):
    item['create_time'] = datetime.datetime.fromtimestamp(item['create_time']).strftime('%Y-%m-%d')
    item['join_time'] = datetime.datetime.fromtimestamp(item['join_time']).strftime('%Y-%m-%d %H:%M:%S')
    item['update_time'] = datetime.datetime.fromtimestamp(item['update_time']).strftime('%Y-%m-%d %H:%M:%S')
    item['expire_time'] = datetime.datetime.fromtimestamp(item['expire_time']).strftime('%Y-%m-%d')
    item['contract_name'] = VARIETY_CN.get(item['variety_en'], '') + item['contract']
    item['annex_url'] = APP_HOST + 'static/' + item['annex_url']
    return item


@investment_api.post('/add/')  # 用户添加一条投资方案(可能含附件)
async def add_investment(annex_file: UploadFile = Form(None),
                         body_item: InvestmentAddBodyItem = Depends(get_investment_content_item)):
    # 验证用户
    user_id, is_audit = validate_operate_user(body_item.user_token, 'investment')
    # 处理body中的数据
    body_item.create_time = int(datetime.datetime.strptime(body_item.create_time, '%Y-%m-%d').timestamp())
    body_item.expire_time = int(datetime.datetime.strptime(body_item.expire_time, '%Y-%m-%d').timestamp())

    body_content = jsonable_encoder(body_item)
    now_timestamp = int(datetime.datetime.now().timestamp())
    body_content['join_time'] = now_timestamp
    body_content['update_time'] = now_timestamp
    body_content['author_id'] = user_id
    body_content['annex'] = ''
    body_content['annex_url'] = ''
    save_path = ''
    if annex_file:  # 有附件
        save_path, sql_path = get_file_paths('INVESTMENT', user_id, annex_file.filename)
        # print(save_path)
        # print(sql_path)
        # 保存附件到指定文件夹
        file_content = await annex_file.read()
        with open(save_path, 'wb') as fp:
            fp.write(file_content)
        await annex_file.close()
        body_content['annex'] = annex_file.filename
        body_content['annex_url'] = sql_path
    # 保存记录到数据库
    with DBWorker() as (_, cursor):
        count = cursor.execute(
            "INSERT INTO work_investment (create_time,join_time,update_time,author_id,title,variety_en,contract,"
            "direction,build_price,out_price,build_hands,cutloss_price,expire_time,profit,note,annex,annex_url,"
            "is_publish,is_running) VALUES (%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,%(title)s,"
            "%(variety_en)s,%(contract)s,%(direction)s,%(build_price)s,%(out_price)s,%(build_hands)s,%(cutloss_price)s,"
            "%(expire_time)s,%(profit)s,%(note)s,%(annex)s,%(annex_url)s,%(is_publish)s,%(is_running)s);",
            body_content
        )
        if count < 1 and save_path and os.path.exists(save_path) and os.path.isfile(save_path):
            # 添加失败,移除文件
            os.remove(save_path)
    return {'message': '添加投资方案成功!'}


@investment_api.post('/')  # 查询用户指定范围内的投资方案,并返回结果
async def get_investment(query_item: QueryInvestmentItem = Body(...)):
    # 验证用户
    audit = 'investment' if query_item.is_audit else None
    user_id, is_audit = validate_operate_user(query_item.user_token, audit)
    start_timestamp, end_timestamp = validate_date_range(query_item.start_date, query_item.end_date)
    # 查询数据
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT ivtb.*,usertb.username "
            "FROM work_investment AS ivtb "
            "INNER JOIN user_user AS usertb ON ivtb.author_id=usertb.id "
            "WHERE ivtb.create_time>%s AND ivtb.create_time<=%s AND IF(1=%s,TRUE,ivtb.author_id=%s) "
            "ORDER BY ivtb.create_time DESC;",
            (start_timestamp, end_timestamp, is_audit, user_id)
        )
        investments = cursor.fetchall()
    investments, _ = filter_records(
        is_audit, query_item.req_staff, query_item.keyword, 'title', investments, [])
    investments = list(map(handle_investment_item, investments))
    return {'message': '获取投资方案成功!', 'investments': investments}


@investment_api.put('/modify/{investment_id}/')  # 用户修改一条投资方案信息
async def modify_investment(investment_id: int,
                            annex_file: UploadFile = Form(None),
                            body_item: InvestmentModifyBodyItem = Depends(get_investment_modify_item)):
    # 验证用户
    user_id, is_audit = validate_operate_user(body_item.user_token, 'investment')
    body_content = jsonable_encoder(body_item)
    now_timestamp = int(datetime.datetime.now().timestamp())
    body_content['update_time'] = now_timestamp
    body_content['is_audit'] = is_audit
    body_content['user_id'] = user_id
    # 保存记录到数据库
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT * FROM work_investment WHERE id=%s AND IF(1=%s,TRUE,author_id=%s);",
            (investment_id, is_audit, user_id)
        )
        investment_obj = cursor.fetchone()
        if not investment_obj:
            raise HTTPException(status_code=400, detail='investment item Not Found')
        # 有附件，删除原来的附件并保存现在的附件
        if annex_file:
            old_annex_url = os.path.join(STATICS_STORAGE, investment_obj['annex_url'])
            save_path, sql_path = get_file_paths('INVESTMENT', user_id, annex_file.filename)

            body_content['annex'] = annex_file.filename
            body_content['annex_url'] = sql_path
            cursor.execute(
                "UPDATE work_investment SET build_price=%(build_price)s,build_hands=%(build_hands)s,"
                "out_price=%(out_price)s,cutloss_price=%(cutloss_price)s,"
                "profit=%(profit)s,is_running=%(is_running)s,score=%(score)s,note=%(note)s,"
                "annex=%(annex)s,annex_url=%(annex_url)s "
                "WHERE id=%(investment_id)s AND IF(1=%(is_audit)s,TRUE,author_id=%(user_id)s)"
                " LIMIT 1;",
                body_content
            )
            # 保存附件到指定文件
            file_content = await annex_file.read()
            with open(save_path, 'wb') as fp:
                fp.write(file_content)
            await annex_file.close()
            if annex_file and os.path.exists(old_annex_url) and os.path.isfile(old_annex_url):
                os.remove(old_annex_url)  # 移除旧文件
        # 没有附件,只更新其他字段
        else:
            cursor.execute(
                "UPDATE work_investment SET build_price=%(build_price)s,build_hands=%(build_hands)s,"
                "out_price=%(out_price)s,cutloss_price=%(cutloss_price)s,"
                "profit=%(profit)s,is_running=%(is_running)s,score=%(score)s,note=%(note)s "
                "WHERE id=%(investment_id)s AND IF(1=%(is_audit)s,TRUE,author_id=%(user_id)s) "
                "LIMIT 1;",
                body_content
            )
    return {'message': '修改成功!'}


@investment_api.delete('/remove/{investment_id}/')  # 用户或管理者删除一条投资方案记录
async def delete_investment_record(investment_id: int, user_token: str = Query(...)):
    user_id, is_audit = validate_operate_user(user_token)
    # 删除数据
    with DBWorker() as (_, cursor):
        cursor.execute('SELECT id,author_id,annex_url FROM work_investment WHERE id=%s;', (investment_id,))
        investment_record = cursor.fetchone()
        if investment_record:
            if is_audit != 1 and investment_record['author_id'] != user_id:
                raise HTTPException(status_code=403, detail='不能删除他人的数据记录!')
            # 删除记录
            cursor.execute(
                "DELETE FROM work_investment WHERE id=%s AND IF(1=%s,TRUE,author_id=%s) LIMIT 1;",
                (investment_id, is_audit, user_id)
            )
            # 删除附件
            if investment_record['annex_url']:
                annex_url = os.path.join(STATICS_STORAGE, investment_record['annex_url'])
                if os.path.exists(annex_url) and os.path.isfile(annex_url):
                    os.remove(annex_url)
            return {'message': '删除成功!'}
        else:
            raise HTTPException(status_code=400, detail='数据不存在!')

