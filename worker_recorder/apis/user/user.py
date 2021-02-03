# _*_ coding:utf-8 _*_

# 用户的API
# 用户的身份情况access见settings.py

# 1. 用户使用账号密码登录
# 2. 用户使用token登录
# 3. 管理用户的列表
# 4. 添加一个用户
# 5. 设置一个用户的模块管理权限
# 6. 用户设置头像

import os
import datetime
from fastapi import APIRouter, Query, Body, HTTPException, UploadFile, Form

from db import DBWorker
from settings import APP_HOST
from utils.encryption import encrypt_password, generate_user_token, decipher_user_token, genetate_user_fixed_code
from utils.constants import ORGANIZATIONS
from utils.file_hands import get_file_paths
from settings import STATICS_STORAGE
from .validate_models import UserLoginItem, UserAddedItem

user_api = APIRouter()


@user_api.post('/login/')  # 登录成功只返回用户的token
async def user_login(user_data: UserLoginItem = Body(...)):
    # 查询用户及密码
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT id,fixed_code,phone,password,access,is_active FROM user_user "
            "WHERE phone=%s OR fixed_code=%s OR username=%s;",
            (user_data.username, user_data.username, user_data.username)
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
    access = user['access'].split('-') if user['access'] else []
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
            "SELECT id,username,avatar,access FROM user_user WHERE id=%s AND is_active=1;",
            (user_id, )
        )
        user = cursor.fetchone()
        # 刷新登录时间
        timestamp_now = int(datetime.datetime.now().timestamp())
        cursor.execute("UPDATE user_user SET update_time=%s WHERE id=%s;", (timestamp_now, user_id))
    if not user:
        raise HTTPException(status_code=401, detail='用户无效!')
    avatar = '{}static/{}'.format(APP_HOST, user['avatar']) if user['avatar'] else '{}static/user_avatar.png'.format(APP_HOST)
    return {
        'avatar': avatar,
        'name': user['username'],
        'user_id': user_id,
        'access': user['access'].split('-')
    }


@user_api.get('/list/')  # 管理员获取用户列表
async def user_list(token: str = Query(...)):
    # 解析token
    user_id, access = decipher_user_token(token)
    if user_id is None or access is None:
        raise HTTPException(status_code=401, detail='登录已过期!')

    # 查询用户列表
    with DBWorker() as (_, cursor):
        # 查询请求用户的organization
        cursor.execute("SELECT id,organization,access FROM user_user WHERE id=%s;", (user_id, ))
        req_user = cursor.fetchone()
        if not req_user:
            raise HTTPException(status_code=401, detail='用户不存在!')
        req_organization = req_user['organization']
        req_access = req_user['access'].split('-')
        cursor.execute(
            "SELECT id,username,fixed_code,join_time,update_time,phone,email,access,is_active,organization "
            "FROM user_user WHERE id>1;"
        )
        users = cursor.fetchall()
    resp_users = []  # 普通用户返回空
    # 管理员返回所有的用户
    if 'admin' in req_access:
        resp_users = users
    # 组长返回组员
    elif 'leader' in req_access:
        for user_item in users:
            if user_item['organization'] == req_organization:
                resp_users.append(user_item)
    # 普通用户返回自己
    else:
        resp_users.append(user_id)
    for user_item in resp_users:
        user_item['join_time'] = datetime.datetime.fromtimestamp(user_item['join_time']).strftime('%Y-%m-%d %H:%M:%S')
        user_item['update_time'] = datetime.datetime.fromtimestamp(user_item['update_time']).strftime('%Y-%m-%d %H:%M:%S')
        user_item['organization_name'] = ORGANIZATIONS.get(user_item['organization'], '未知')
        user_item['access'] = user_item['access'].split('-')
        user_item['is_leader'] = 1 if 'leader' in user_item['access'] else 0
    return {'message': '获取用户列表成功!', 'users': resp_users}


@user_api.post('/add/')  # 添加一个用户
async def add_user(user_item: UserAddedItem = Body(...)):
    # 验证添加这是否为管理员
    operate_id, access = decipher_user_token(user_item.operate_token)
    if 'admin' not in access:
        raise HTTPException(status_code=403, detail='您没有权限进行此操作!')
    int_timestamp = int(datetime.datetime.now().timestamp())
    new_user = {
        'join_time': int_timestamp,
        'update_time': int_timestamp,
        'username': user_item.username,
        'fixed_code': genetate_user_fixed_code(),
        'password': encrypt_password(user_item.password),
        'phone': user_item.phone,
        'organization': user_item.organization
    }
    with DBWorker() as (_, cursor):
        cursor.execute(
            "INSERT INTO user_user (join_time,update_time,username,fixed_code,password,phone,organization) "
            "VALUES (%(join_time)s,%(update_time)s,%(username)s,%(fixed_code)s,%(password)s,%(phone)s,"
            "%(organization)s);",
            new_user
        )
        # new_user_id = cursor.lastrowid
    return {'message': '创建新用户成功!'}


@user_api.post('/access/')   # 设置一个用户的权限
async def set_user_access(user_id: int = Body(..., embed=True),
                          user_access: list = Body(..., embed=True),
                          user_token: str = Query(...)):
    user_access = list(filter(lambda x: True if x else False, user_access))
    operate_id, access = decipher_user_token(user_token)
    if not operate_id:
        raise HTTPException(status_code=401, detail='登录过期了')
    if 'admin' not in access:
        raise HTTPException(status_code=403, detail='您不能这样做!')
    # 设置权限
    with DBWorker() as (_, cursor):
        cursor.execute(
            "UPDATE user_user SET access=%s WHERE id=%s;",
            ('-'.join(user_access), user_id)
        )
    return {'message': '设置成功!'}


@user_api.post('/avatar/')  # 用户设置头像
async def user_set_avatar(avatar_file: UploadFile = Form(...), user_token: str = Form(...)):
    # 解析用户
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期了!请重新登录!')
    # 读取头像图片文件
    save_path, sql_path = get_file_paths('Avatars', user_id, avatar_file.filename, folder_root='User', hashed=True)
    # 保存文件并更新数据库
    file_content = await avatar_file.read()
    with open(save_path, 'wb') as fp:
        fp.write(file_content)
    await avatar_file.close()
    with DBWorker() as (_, cursor):
        # 查询历史头像路径
        cursor.execute("SELECT id,avatar FROM user_user WHERE id=%s;", (user_id, ))
        user_obj = cursor.fetchone()
        cursor.execute("UPDATE user_user SET avatar=%s WHERE id=%s;", (sql_path, user_id))
        if user_obj:
            old_avatar = os.path.join(STATICS_STORAGE, user_obj['avatar'])
            if os.path.exists(old_avatar) and os.path.isfile(old_avatar):
                os.remove(old_avatar)
    return {'message': '修改成功!', 'avatar_url': '{}static/{}'.format(APP_HOST, sql_path)}


@user_api.get('/message/count/')  # 用户的未读消息数
async def unread_message_count():
    return {'count': 0}


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
