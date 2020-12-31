# _*_ coding:utf-8 _*_
# @File  : message.py
# @Time  : 2020-12-29 11:21
# @Author: zizle

# 1. 用户上传短讯通文件数据
# 2. 用户删除自己的一条短讯通或管理员删除一条短讯通
# 3. 用户获取自己的短讯通数据(分页)
# 4. POST-管理者获取待批注数据(分页)
# 5. PUT-管理者进行批注

import datetime

import pandas as pd
from fastapi import APIRouter, UploadFile, Form, HTTPException, Query, Body

from db import DBWorker
from utils.encryption import decipher_user_token
from utils.file_hands import date_column_converter
from utils.constants import MSG_AUDIT_MIND
from logger import logger
from .validate_models import AuditMsgBodyItem, AuditMessageItem

message_api = APIRouter()


# 处理短讯通返回数据的内容
def handler_message_content(m_item):
    m_item['create_time'] = datetime.datetime.fromtimestamp(m_item['create_time']).strftime('%Y-%m-%d')
    m_item['update_time'] = datetime.datetime.fromtimestamp(m_item['update_time']).strftime('%Y-%m-%d %H:%M:%S')
    m_item['audit_description'] = '批注意见：{}'.format(MSG_AUDIT_MIND.get(m_item['audit_mind'], '无'))
    return m_item

# 过滤短信通指定以外的作者



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
    # 查询系统中当前用户最大的短信通信息日期
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT MAX(create_time) AS max_date FROM work_short_message WHERE author_id=%s;",
            (user_id, )
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
                "INSERT INTO work_short_message(create_time,update_time,author_id,content,msg_type,effects,note) "
                "VALUES (%(create_time)s,%(update_time)s,%(author_id)s,%(content)s,%(msg_type)s,%(effects)s,%(note)s);",
                save_msg
            )
            # 查出刚刚插入的数据
            cursor.execute(
                "SELECT id,create_time,update_time,author_id,content,msg_type,effects,note,audit_mind,is_active "
                "FROM work_short_message WHERE update_time=%s AND author_id=%s;",
                (now_timestamp, user_id)
            )
            message_saved = cursor.fetchall()
            for new_item in message_saved:
                new_item['create_time'] = datetime.datetime.fromtimestamp(
                    new_item['create_time']).strftime('%Y-%m-%d')
    return {'message': '上传数据成功!新增{}条。'.format(len(message_saved)), 'messages': message_saved}


@message_api.get('/')  # 用户分页获取自己的短讯通数据
async def get_message(user_token: str = Query(...), page: int = Query(1, ge=1), page_size: int = Query(1, ge=1)):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期了!请重新登录.')
    # 分页查询数据
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT id,create_time,update_time,content,msg_type,effects,note,audit_mind,is_active "
            "FROM work_short_message WHERE author_id=%s ORDER BY create_time DESC LIMIT %s,%s;",
            (user_id, (page - 1) * page_size, page_size)
        )
        messages = cursor.fetchall()
        # 查询总数量
        cursor.execute("SELECT count(id) as total_count FROM work_short_message WHERE author_id=%s;", (user_id, ))
        total_obj = cursor.fetchone()
        total_count = total_obj['total_count'] if total_obj['total_count'] else 0
    messages = list(map(handler_message_content, messages))
    return {'message': '获取数据成功!', 'messages': messages, 'page': page, 'total_count': total_count}


@message_api.post('/audit/')  # 管理员查询要批注短讯通数据
async def audit_message(body_item: AuditMsgBodyItem = Body(...)):
    operate_id, access = decipher_user_token(body_item.user_token)
    if not operate_id:
        raise HTTPException(status_code=401, detail='登录过期!请重新登录。')
    if 'admin' not in access and 'short_message' not in access:
        raise HTTPException(status_code=403, detail='不能这样操作!')
    # 处理时间区域
    try:
        start_date = int(datetime.datetime.strptime(body_item.start_date, '%Y-%m-%d').timestamp())
        end_date = int(datetime.datetime.strptime(body_item.end_date, '%Y-%m-%d').timestamp())
        if start_date == end_date:
            end_date = int((datetime.datetime.fromtimestamp(end_date) + datetime.timedelta(days=1)).timestamp())
        if start_date > end_date:
            raise ValueError('Error')
    except ValueError:
        raise HTTPException(status_code=400, detail='参数错误!')
    # 查询数据分页
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT msgtb.id,msgtb.create_time,msgtb.update_time,msgtb.author_id,msgtb.content,"
            "msgtb.msg_type,msgtb.effects,msgtb.note,msgtb.audit_mind,msgtb.is_active,"
            "usertb.username "
            "FROM work_short_message AS msgtb "
            "INNER JOIN user_user AS usertb ON usertb.id=msgtb.author_id "
            "WHERE msgtb.create_time>=%s AND msgtb.create_time <= %s "
            "ORDER BY msgtb.create_time DESC;",
            (start_date, end_date)
        )
        messages = cursor.fetchall()
        # 查询总数量
        cursor.execute("SELECT msgtb.id,msgtb.author_id,msgtb.content "
                       "FROM work_short_message AS msgtb "
                       "INNER JOIN user_user AS usertb ON usertb.id=msgtb.author_id "
                       "WHERE msgtb.create_time>=%s AND msgtb.create_time <= %s;",
                       (start_date, end_date))
        total_messages = cursor.fetchall()
    # 过滤数据(处理作者)
    if body_item.req_staff:
        messages = list(filter(lambda x: x['author_id'] in body_item.req_staff, messages))
        total_messages = list(filter(lambda x: x['author_id'] in body_item.req_staff, total_messages))
    # 过滤数据(处理关键字)
    if body_item.keyword:
        messages = list(filter(lambda x: body_item.keyword in x['content'], messages))
        total_messages = list(filter(lambda x: body_item.keyword in x['content'], total_messages))
    # 截取数据
    messages = messages[(body_item.page - 1) * body_item.page_size: body_item.page_size * body_item.page]
    # 处理数据内容
    messages = list(map(handler_message_content, messages))

    return {'message': '获取数据成功!', 'messages': messages, 'page': body_item.page, 'total_count': len(total_messages)}


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
            "SELECT id,author_id,audit_mind FROM work_short_message WHERE id=%s;", (msg_id, )
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
                "DELETE FROM work_short_message WHERE id=%s AND IF(1=%s,TRUE,author_id=%s);",
                (msg_id, is_admin, user_id)
            )
            return {'message': '删除成功!'}
        else:
            raise HTTPException(status_code=403, detail=err_message)
