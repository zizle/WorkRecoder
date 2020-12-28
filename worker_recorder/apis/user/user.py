# _*_ coding:utf-8 _*_


# 用户的API

# 1. 用户使用账号密码登录
# 2. 用户使用token登录
# 3. 管理关联用户的列表
#

import datetime
from fastapi import APIRouter, Query, Body, HTTPException

from db import DBWorker
from settings import APP_HOST
from utils.encryption import encrypt_password, generate_user_token, decipher_user_token
from utils.constants import ORGANIZATIONS
from .validate_models import UserLoginItem

user_api = APIRouter()


@user_api.post('/login/')  # 登录成功只返回用户的token
async def user_login(user_data: UserLoginItem = Body(...)):
    # 查询用户及密码
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT id,fixed_code,phone,password,is_admin,is_active FROM user_user WHERE phone=%s OR fixed_code=%s;",
            (user_data.username, user_data.username)
        )
        user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail='用户不存在!')
    if not user['is_active']:
        raise HTTPException(status_code=401, detail='无效用户!')
    # 对比hash密码
    if user['password'] != encrypt_password(user_data.password):
        raise HTTPException(status_code=401, detail='用户名或密码错误!')
    # 生成token
    access = ['admin', 'normal'] if user['is_admin'] else ['normal']
    user_token = generate_user_token({'user_id': user['id'], 'access': access})
    return {'message': '登录成功!', 'token': user_token}


@user_api.get('/info/')  # 用户拿着登录成功的token再来请求具体信息
async def user_information(token: str = Query(...)):
    # 解析token
    user_id, access = decipher_user_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail='登录已过期!')
    # 查询用户信息
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT id,username,is_admin FROM user_user WHERE id=%s AND is_active=1;",
            (user_id, )
        )
        user = cursor.fetchone()
        # 刷新登录时间
        timestamp_now = int(datetime.datetime.now().timestamp())
        cursor.execute("UPDATE user_user SET update_time=%s WHERE id=%s;", (timestamp_now, user_id))
    if not user:
        raise HTTPException(status_code=401, detail='用户无效!')
    return {
        'avatar': '{}static/user_avatar.png'.format(APP_HOST),
        'name': user['username'],
        'user_id': user_id,
        'access': access
    }


@user_api.get('/list/')
async def user_list(token: str = Query(...)):
    # 解析token
    user_id, access = decipher_user_token(token)
    if user_id is None or access is None:
        raise HTTPException(status_code=401, detail='登录已过期!')
    if 'admin' not in access:
        return {'message': '获取用户列表成功!', 'users': []}
    # 查询用户列表
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT id,username,fixed_code,join_time,update_time,phone,email,is_admin,is_active,organization "
            "FROM user_user;"
        )
        users = cursor.fetchall()
    for user_item in users:
        user_item['join_time'] = datetime.datetime.fromtimestamp(user_item['join_time']).strftime('%Y-%m-%d %H:%M:%S')
        user_item['update_time'] = datetime.datetime.fromtimestamp(user_item['update_time']).strftime('%Y-%m-%d %H:%M:%S')
        user_item['organization_name'] = ORGANIZATIONS.get(user_item['organization'], '未知')
    return {'message': '获取用户列表成功!', 'users': users}


@user_api.get('/message/count/')  # 用户的未读消息数
async def unread_message_count():
    return {'count': 5}


@user_api.get('/message/init/')   # 初始化信息页面
async def init_message():
    return {
        'readed': [{'msg_id': 1, 'create_time': '2020-12-26', 'title': '已读消息的第一条'}],
        'trash': [{'msg_id': i, 'create_time': '2020-12-25', 'title': '明天过来一下'} for i in range(5, 1000)],
        'unread': [
            {'msg_id': i, 'create_time': '2020-12-27', 'title': '这是啥东西'} for i in range(5)
        ],
    }


@user_api.get('/message/content/')  # 获取一条消息的内容
async def message_content(msg_id: int = Query(...)):
    print('获取msg_id:', msg_id)
    return {'content': '<div>这是id = {} 消息的内容:\n{}</div>'.format(msg_id, '新增内容')}


@user_api.post('/message/has-read/')  # 用户已读一条信息
async def message_has_read(msg_id: int = Body(..., embed=True)):
    print('已读：', msg_id)
    return {'message': '消息已读!'}


@user_api.post('/message/remove-readed/')  # 删除一条已读到回收站
async def remove_readed(msg_id: int = Body(..., embed=True)):
    print('移到回收站：', msg_id)
    return {'message': '移到回收站!'}


@user_api.post('/message/restore/')  # 移动回收站到已读
async def remove_readed(msg_id: int = Body(..., embed=True)):
    print('移到已读：', msg_id)
    return {'message': '移到已读!'}
