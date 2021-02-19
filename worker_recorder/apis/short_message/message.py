# _*_ coding:utf-8 _*_
# @File  : message.py
# @Time  : 2020-12-29 11:21
# @Author: zizle

# 1. 用户上传短讯通文件数据
# 2. 用户删除自己的一条短讯通或管理员删除一条短讯通
# 3. 用户删除本次excel上传的所有数据(根据join_time)
# 4. POST-用户或批注管理者获取短讯通数据(分页)
# 5. PUT-管理者进行批注

import datetime

import pandas as pd
from fastapi import APIRouter, UploadFile, Form, HTTPException, Query, Body
from fastapi.encoders import jsonable_encoder

from db import DBWorker
from utils.encryption import decipher_user_token
from utils.file_hands import date_column_converter
from utils.constants import MSG_AUDIT_MIND
from apis.tools import validate_operate_user, validate_date_range, filter_records
from logger import logger
from .validate_models import AuditMessageItem, QueryMsgBodyItem, JoinTimeDelMsgItem, AddMsgBodyItem


message_api = APIRouter()


# 处理短讯通返回数据的内容
def handler_message_content(m_item):
    m_item['create_time'] = datetime.datetime.fromtimestamp(m_item['create_time']).strftime('%Y-%m-%d')
    m_item['join_time'] = datetime.datetime.fromtimestamp(m_item['join_time']).strftime('%Y-%m-%d %H:%M:%S')
    m_item['update_time'] = datetime.datetime.fromtimestamp(m_item['update_time']).strftime('%Y-%m-%d %H:%M:%S')
    m_item['audit_description'] = '批注意见：{}'.format(MSG_AUDIT_MIND.get(m_item['audit_mind'], '无'))
    return m_item


@message_api.post('/excel/')
async def excel_short_message(excel_file: UploadFile = Form(...), user_token: str = Form(...)):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录已过期,请重新登录!')
    # 解析文件
    try:
        file_contents = await excel_file.read()
        file = pd.ExcelFile(file_contents)
        # 读取表格
        msg_df = file.parse('短讯通记录', converters={0: date_column_converter})
        await excel_file.close()
    except Exception as e:
        logger.error('用户{}上传短信通数据错误:{}'.format(user_id, e))
        raise HTTPException(status_code=403, detail='文件格式错误,无法处理!另请确认Sheet名为【短讯通记录】')
    # 验证数据表头
    headers = list(msg_df.columns)
    if headers != ['日期', '信息内容', '类别', '影响品种', '备注']:
        raise HTTPException(status_code=403, detail='文件表头格式有误,正确的为【日期, 信息内容, 类别, 影响品种, 备注】')
    msg_df.columns = ['create_time', 'content', 'msg_type', 'effects', 'note']
    # 去除日期为nan的行
    msg_df.dropna(subset=['create_time'], inplace=True)
    # 填充其他nan为‘’
    msg_df.fillna(value='', inplace=True)
    # 添加author列
    msg_df['author_id'] = [user_id for _ in range(msg_df.shape[0])]
    # 添加update_time列
    now_timestamp = int(datetime.datetime.now().timestamp())
    msg_df['update_time'] = [now_timestamp for _ in range(msg_df.shape[0])]
    msg_df['join_time'] = [now_timestamp for _ in range(msg_df.shape[0])]
    # 查询系统中当前用户最大的短信通信息日期
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT MAX(create_time) AS max_date FROM work_short_message WHERE author_id=%s;",
            (user_id,)
        )
        current_max_date = cursor.fetchone()['max_date']
        if current_max_date is None:
            current_max_date = 0
        # 截取数据
        msg_df = msg_df[msg_df['create_time'] > current_max_date]
        # 保存数据
        save_msg = msg_df.to_dict(orient='records')
        message_saved = []
        if not msg_df.empty:
            cursor.executemany(
                "INSERT INTO work_short_message(create_time,join_time,update_time,author_id,content,"
                "msg_type,effects,note) VALUES "
                "(%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,%(content)s,"
                "%(msg_type)s,%(effects)s,%(note)s);",
                save_msg
            )
            # 查出刚刚插入的数据
            cursor.execute(
                "SELECT id,create_time,update_time,author_id,content,msg_type,effects,note,audit_mind,is_active "
                "FROM work_short_message WHERE join_time=%s AND author_id=%s;",
                (now_timestamp, user_id)
            )
            message_saved = cursor.fetchall()
            for new_item in message_saved:
                new_item['create_time'] = datetime.datetime.fromtimestamp(
                    new_item['create_time']).strftime('%Y-%m-%d')
    return {'message': '上传数据成功!新增{}条。'.format(len(message_saved)),
            'messages': message_saved, 'join_time': now_timestamp}


@message_api.delete('/excel/')  # 用户删除本次excel上传的所有数据(根据join_time)
async def delete_with_join_time(del_item: JoinTimeDelMsgItem = Body(...)):
    user_id, _ = decipher_user_token(del_item.user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期了,请重新登录!')
    # 根据join_time删除相应的数据
    with DBWorker() as (_, cursor):
        count = cursor.execute(
            "DELETE FROM work_short_message WHERE author_id=%s AND join_time=%s;",
            (user_id, del_item.join_time)
        )
    return {'message': '删除成功!本次删除条目数量:{}'.format(count)}


@message_api.post('/', )  # POST-分页获取短讯通数据(包含待批注数据获取)
async def query_short_message(body_item: QueryMsgBodyItem):
    audit = 'short_message' if body_item.is_audit else None
    user_id, is_audit = validate_operate_user(body_item.user_token, audit)
    # # 处理时间区域
    start_date, end_date = validate_date_range(body_item.start_date, body_item.end_date)
    # 查询数据
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT msgtb.id,msgtb.create_time,msgtb.join_time,msgtb.update_time,msgtb.author_id,msgtb.content,"
            "msgtb.msg_type,msgtb.effects,msgtb.note,msgtb.audit_mind,msgtb.is_active,"
            "usertb.username "
            "FROM work_short_message AS msgtb "
            "INNER JOIN user_user AS usertb ON usertb.id=msgtb.author_id "
            "WHERE msgtb.create_time>=%s AND msgtb.create_time <= %s AND IF(1=%s,TRUE,msgtb.author_id=%s) "
            "ORDER BY msgtb.create_time DESC;",
            (start_date, end_date, is_audit, user_id)
        )
        messages = cursor.fetchall()
        # 查询总数量
        cursor.execute(
            "SELECT msgtb.id,msgtb.author_id,msgtb.content "
            "FROM work_short_message AS msgtb "
            "INNER JOIN user_user AS usertb ON usertb.id=msgtb.author_id "
            "WHERE msgtb.create_time>=%s AND msgtb.create_time <= %s AND IF(1=%s,TRUE,msgtb.author_id=%s);",
            (start_date, end_date, is_audit, user_id)
        )
        total_messages = cursor.fetchall()
    messages, total_messages = filter_records(
        is_audit, body_item.req_staff, body_item.keyword, 'content', messages, total_messages)
    # 截取数据(分页)
    messages = messages[(body_item.page - 1) * body_item.page_size: body_item.page_size * body_item.page]
    # 处理数据内容
    messages = list(map(handler_message_content, messages))
    return {'message': '获取数据成功!', 'messages': messages, 'page': body_item.page, 'total_count': len(total_messages)}


@message_api.post('/add/')  # POST-添加一条短讯通数据
async def add_short_message(body_item: AddMsgBodyItem):
    # 解析用户保存数据
    user_id, access = decipher_user_token(body_item.user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录已过期,请重新登录!')
    now_timestamp = int(datetime.datetime.now().timestamp())
    shotmsg_add = jsonable_encoder(body_item)
    shotmsg_add['create_time'] = int(datetime.datetime.strptime(body_item.create_time, '%Y-%m-%d').timestamp())
    shotmsg_add['join_time'] = now_timestamp
    shotmsg_add['update_time'] = now_timestamp
    shotmsg_add['author_id'] = user_id
    del shotmsg_add['user_token']
    with DBWorker() as (_, cursor):
        cursor.execute(
            "INSERT INTO work_short_message (create_time,join_time,update_time,author_id,content,msg_type,"
            "effects,note) "
            "VALUES (%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,%(content)s,%(msg_type)s,"
            "%(effects)s,%(note)s);",
            shotmsg_add
        )
    return {'message': '添加成功!'}

@message_api.put('/audit/{msg_id}/')  # 修改一条短讯通的批注
async def update_message_audit(msg_id: int, body_item: AuditMessageItem = Body(...)):
    operate_id, access = decipher_user_token(body_item.user_token)
    if not operate_id:
        raise HTTPException(status_code=401, detail='登录过期!请重新登录。')
    if 'admin' not in access and 'short_message' not in access:
        raise HTTPException(status_code=403, detail='不能这样操作!')
    # 修改数据
    with DBWorker() as (_, cursor):
        cursor.execute(
            "UPDATE work_short_message SET audit_mind=%s WHERE id=%s;", (body_item.audit_mind, msg_id)
        )
    audit_description = '批注意见：{}'.format(MSG_AUDIT_MIND.get(body_item.audit_mind, '无'))
    return {'message': '修改成功!', 'audit_description': audit_description, 'audit_mind': body_item.audit_mind}


@message_api.delete('/{msg_id}/')  # 删除一条短信通
async def delete_short_message(msg_id: int, user_token: str = Query(...)):
    user_id, access = decipher_user_token(user_token)
    is_admin = 0
    if 'admin' in access or 'short_message' in access:
        is_admin = 1
    # 删除数据
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT id,author_id,audit_mind FROM work_short_message WHERE id=%s;", (msg_id,)
        )
        msg_record = cursor.fetchone()
        can_delete = True
        err_message = '已成功删除!'
        if msg_record:
            if msg_record['author_id'] != user_id and is_admin == 0:
                can_delete = False
                err_message = '您不能删除他人的记录!'
            if msg_record['audit_mind'] != 0 and is_admin == 0:
                can_delete = False
                err_message = '已批注过的信息请联系管理员删除!'
        if can_delete:
            cursor.execute(
                "DELETE FROM work_short_message WHERE id=%s AND IF(1=%s,TRUE,author_id=%s) LIMIT 1;",
                (msg_id, is_admin, user_id)
            )
            return {'message': '删除成功!'}
        else:
            raise HTTPException(status_code=403, detail=err_message)
