# _*_ coding:utf-8 _*_


# 用户的API

# 1. 管理员添加职员
# 2. 职员使用账号密码登录
# 3. 职员修改密码

from fastapi import APIRouter, Query, Body

from settings import APP_HOST
from .validate_models import UserLoginItem

user_api = APIRouter()


@user_api.post('/login/')  # 登录成功只返回用户的token
async def user_login(user_data: UserLoginItem = Body(...)):
    print(user_data)
    return {'token': 'xafisdfofnjaklsdfa'}


@user_api.get('/info/')  # 用户拿着登录成功的token再来请求具体信息
async def user_information(token: str = Query(...)):
    print('token:', token)
    return {
        'avatar': '{}static/user_avatar.jpg'.format(APP_HOST),
        'name': '天生我才',
        'user_id': 1,
        'access': ['super_admin']
    }


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
