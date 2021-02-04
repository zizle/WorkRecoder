# _*_ coding:utf-8 _*_
# @File  : abnormal.py
# @Time  : 2021-01-12 10:10
# @Author: zizle

import os
import datetime
from fastapi import APIRouter, UploadFile, Form, Depends, Body, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from apis.tools import validate_operate_user, validate_date_range, filter_records
from utils.file_hands import get_file_paths
from db import DBWorker
from settings import APP_HOST, STATICS_STORAGE
from .validate_models import (AbnormalWorkAddItem, get_abnormal_content_item, QueryAbnormalItem,
                              AbnormalModifyBodyItem, get_abnormal_modify_item,
                              AuditAbnormalItem)


abnormal_api = APIRouter()


def handle_abnormal_item(item):
    item['create_time'] = datetime.datetime.fromtimestamp(item['create_time']).strftime('%Y-%m-%d')
    item['join_time'] = datetime.datetime.fromtimestamp(item['join_time']).strftime('%Y-%m-%d %H:%M:%S')
    item['update_time'] = datetime.datetime.fromtimestamp(item['update_time']).strftime('%Y-%m-%d %H:%M:%S')
    item['annex_url'] = APP_HOST + 'static/' + item['annex_url']
    return item


@abnormal_api.post('/add/')  # 用户添加一条非常规工作记录(可能含附件)
async def add_abnormal_work(annex_file: UploadFile = Form(None),
                            body_item: AbnormalWorkAddItem = Depends(get_abnormal_content_item)):
    # 验证用户
    user_id, is_audit = validate_operate_user(body_item.user_token, 'abnormal')
    # 处理body中的数据
    body_item.create_time = int(datetime.datetime.strptime(body_item.create_time, '%Y-%m-%d').timestamp())
    body_content = jsonable_encoder(body_item)
    now_timestamp = int(datetime.datetime.now().timestamp())
    body_content['join_time'] = now_timestamp
    body_content['update_time'] = now_timestamp
    body_content['author_id'] = user_id
    body_content['annex'] = ''
    body_content['annex_url'] = ''
    save_path = ''
    if annex_file:  # 有附件
        save_path, sql_path = get_file_paths('ABNORMAL', user_id, annex_file.filename)
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
            "INSERT INTO work_abnormal (create_time,join_time,update_time,author_id,title,task_type,sponsor,"
            "applicant,phone,swiss_coin,allowance,partner,note,annex,annex_url) "
            "VALUES (%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,%(title)s,"
            "%(task_type)s,%(sponsor)s,%(applicant)s,%(phone)s,%(swiss_coin)s,%(allowance)s,%(partner)s,"
            "%(note)s,%(annex)s,%(annex_url)s);",
            body_content
        )
        if count < 1 and save_path and os.path.exists(save_path) and os.path.isfile(save_path):
            # 添加失败,移除文件
            os.remove(save_path)
    return {'message': '添加非常规工作成功!'}


@abnormal_api.post('/')  # 查询用户指定范围内的非常规工作,并返回结果
async def get_abnormal_work(query_item: QueryAbnormalItem = Body(...)):
    # 验证用户
    audit = 'abnormal' if query_item.is_audit else None
    user_id, is_audit = validate_operate_user(query_item.user_token, audit)
    start_timestamp, end_timestamp = validate_date_range(query_item.start_date, query_item.end_date)
    # 查询数据
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT abtb.*,usertb.username "
            "FROM work_abnormal AS abtb "
            "INNER JOIN user_user AS usertb ON abtb.author_id=usertb.id "
            "WHERE abtb.create_time>%s AND abtb.create_time<=%s AND IF(1=%s,TRUE,abtb.author_id=%s) "
            "ORDER BY abtb.create_time DESC;",
            (start_timestamp, end_timestamp, is_audit, user_id)
        )
        abnormal_works = cursor.fetchall()
    abnormal_works, _ = filter_records(
        is_audit, query_item.req_staff, query_item.keyword, 'title', abnormal_works, [])
    abnormal_works = list(map(handle_abnormal_item, abnormal_works))
    return {'message': '获取非常规工作成功!', 'abnormal_works': abnormal_works}


@abnormal_api.put('/modify/{abnormal_id}/')  # 用户修改一条非常规工作的信息
async def modify_investment(abnormal_id: int,
                            annex_file: UploadFile = Form(None),
                            body_item: AbnormalModifyBodyItem = Depends(get_abnormal_modify_item)):
    # 验证用户
    user_id, is_audit = validate_operate_user(body_item.user_token, 'abnormal')
    body_content = jsonable_encoder(body_item)
    now_timestamp = int(datetime.datetime.now().timestamp())
    body_content['update_time'] = now_timestamp
    body_content['is_audit'] = is_audit
    body_content['user_id'] = user_id
    # 保存记录到数据库
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT * FROM work_abnormal WHERE id=%s AND IF(1=%s,TRUE,author_id=%s);",
            (abnormal_id, is_audit, user_id)
        )
        abnormal_obj = cursor.fetchone()
        if not abnormal_obj:
            raise HTTPException(status_code=400, detail='abnormal item Not Found')
        # 有附件，删除原来的附件并保存现在的附件
        if annex_file:
            old_annex_url = os.path.join(STATICS_STORAGE, abnormal_obj['annex_url'])
            save_path, sql_path = get_file_paths('ABNORMAL', user_id, annex_file.filename)
            body_content['annex'] = annex_file.filename
            body_content['annex_url'] = sql_path
            cursor.execute(
                "UPDATE work_abnormal SET title=%(title)s,sponsor=%(sponsor)s,applicant=%(applicant)s,"
                "allowance=%(allowance)s,phone=%(phone)s,swiss_coin=%(swiss_coin)s,partner=%(partner)s,score=%(score)s,"
                "note=%(note)s,annex=%(annex)s,annex_url=%(annex_url)s "
                "WHERE id=%(abnormal_id)s AND IF(1=%(is_audit)s,TRUE,author_id=%(user_id)s)"
                " LIMIT 1;",
                body_content
            )
            # 保存附件到指定文件
            file_content = await annex_file.read()
            with open(save_path, 'wb') as fp:
                fp.write(file_content)
            await annex_file.close()
            if os.path.exists(old_annex_url) and os.path.isfile(old_annex_url):
                os.remove(old_annex_url)  # 移除旧文件
        # 没有附件,只更新其他字段
        else:
            cursor.execute(
                "UPDATE work_abnormal SET title=%(title)s,sponsor=%(sponsor)s,applicant=%(applicant)s,"
                "allowance=%(allowance)s,phone=%(phone)s,swiss_coin=%(swiss_coin)s,partner=%(partner)s,score=%(score)s,"
                "note=%(note)s "
                "WHERE id=%(abnormal_id)s AND IF(1=%(is_audit)s,TRUE,author_id=%(user_id)s)"
                " LIMIT 1;",
                body_content
            )
    return {'message': '修改成功!'}


@abnormal_api.put('/audit/{abnormal_id}/')   # 管理员修改一条非常规工作的分数和有效状态
async def audit_abnormal_record(audit_item: AuditAbnormalItem = Body(...)):
    user_id, is_audit = validate_operate_user(audit_item.user_token, 'abnormal')
    if not user_id:
        raise HTTPException(status_code=401, detail='登录已过期!请重新登录!')
    if not is_audit:
        raise HTTPException(status_code=403, detail='没有权限进行此操作!')
    # 修改分数和状态
    is_examined = 1 if audit_item.is_examined else 0
    with DBWorker() as (_, cursor):
        cursor.execute(
            "UPDATE work_abnormal SET score=%s, is_examined=%s WHERE id=%s;",
            (audit_item.score, is_examined, audit_item.abnormal_id)
        )
    return {'message': '修改成功!', 'score': audit_item.score, 'is_examined': audit_item.is_examined}


@abnormal_api.delete('/remove/{abnormal_id}/')  # 用户或管理者删除一条非常规工作
async def delete_investment_record(abnormal_id: int, user_token: str = Query(...)):
    user_id, is_audit = validate_operate_user(user_token)
    # 删除数据
    with DBWorker() as (_, cursor):
        cursor.execute('SELECT id,author_id,annex_url FROM work_abnormal WHERE id=%s;', (abnormal_id,))
        abnormal_record = cursor.fetchone()
        if abnormal_record:
            if is_audit != 1 and abnormal_record['author_id'] != user_id:
                raise HTTPException(status_code=403, detail='不能删除他人的数据记录!')
            # 删除记录
            cursor.execute(
                "DELETE FROM work_abnormal WHERE id=%s AND IF(1=%s,TRUE,author_id=%s) LIMIT 1;",
                (abnormal_id, is_audit, user_id)
            )
            # 删除附件
            if abnormal_record['annex_url']:
                annex_url = os.path.join(STATICS_STORAGE, abnormal_record['annex_url'])
                if os.path.exists(annex_url) and os.path.isfile(annex_url):
                    os.remove(annex_url)
            return {'message': '删除成功!'}
        else:
            raise HTTPException(status_code=400, detail='数据不存在!')
