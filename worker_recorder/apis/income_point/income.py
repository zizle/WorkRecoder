# _*_ coding:utf-8 _*_
# @File  : income.py
# @Time  : 2021-01-13 10:47
# @Author: zizle

# 收入指标模块
# 1. 新增一个客户信息
# 2. 为一个客户增加一条指标信息

import datetime
from fastapi import APIRouter, Body, HTTPException, Query, Depends
from fastapi.encoders import jsonable_encoder
from utils.encryption import decipher_user_token
from apis.tools import validate_operate_user
from db import DBWorker
from .validate_models import AddCustomerItem, AddCustomerIndexItem, ModifyCustomerIndexItem, get_modify_index_item

income_api = APIRouter()


def handle_customer_item(item):
    item['create_time'] = datetime.datetime.fromtimestamp(item['create_time']).strftime('%Y-%m-%d')
    item['join_time'] = datetime.datetime.fromtimestamp(item['join_time']).strftime('%Y-%m-%d %H:%M:%S')
    item['update_time'] = datetime.datetime.fromtimestamp(item['update_time']).strftime('%Y-%m-%d %H:%M:%S')
    return item


@income_api.get('/customers/')  # 获取当前用户的所有客户
async def get_customers(user_token: str = Query(...)):
    user_id, access = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期了,请重新登录!')
    with DBWorker() as (_, cursor):
        cursor.execute("SELECT * FROM work_customer WHERE author_id=%s;", (user_id,))
        all_customer = cursor.fetchall()
    all_customer = list(map(handle_customer_item, all_customer))
    return {'message': '查询成功!', 'customers': all_customer}


@income_api.post('/customer/add/')  # 新增一个客户信息
async def add_customer(customer_item: AddCustomerItem = Body(...)):
    user_id, access = decipher_user_token(customer_item.user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期了,请重新登录!')
    customer_content = jsonable_encoder(customer_item)
    now_timestamp = int(datetime.datetime.now().timestamp())
    customer_content['create_time'] = now_timestamp
    customer_content['join_time'] = now_timestamp
    customer_content['update_time'] = now_timestamp
    customer_content['author_id'] = user_id
    # 加入
    with DBWorker() as (_, cursor):
        cursor.execute(
            "INSERT INTO work_customer (create_time,join_time,update_time,author_id,customer_name,account,"
            "note) "
            "VALUES (%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,%(customer_name)s,%(account)s,"
            "%(note)s);",
            customer_content
        )
        # 查询当前用户的所有客户
        cursor.execute("SELECT * FROM work_customer WHERE author_id=%s;", (user_id, ))
        all_customer = cursor.fetchall()
    all_customer = list(map(handle_customer_item, all_customer))
    return {'message': '添加成功!', 'customers': all_customer}


@income_api.post('/customer/index/add/')  # 为一个客户增加一条指标信息
async def add_customer_index(index_item: AddCustomerIndexItem = Body(...)):
    user_id, access = decipher_user_token(index_item.user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='登录过期了,请重新登录!')
    index_content = jsonable_encoder(index_item)
    now_timestamp = int(datetime.datetime.now().timestamp())
    index_content['join_time'] = now_timestamp
    index_content['update_time'] = now_timestamp
    index_content['create_time'] = int(datetime.datetime.strptime(index_item.create_time, '%Y-%m-%d').timestamp())
    # 添加记录
    with DBWorker() as (_, cursor):
        # 需为本人客户才可进行添加
        cursor.execute("SELECT id FROM work_customer WHERE id=%s AND author_id=%s;", (index_item.customer_id, user_id))
        customer_obj = cursor.fetchone()
        if customer_obj:
            # 查询今日数据是否存在
            cursor.execute(
                "SELECT id FROM work_customer_index WHERE customer_id=%s AND create_time=%s;",
                (index_content['customer_id'], index_content['create_time'])
            )
            if cursor.fetchone():
                raise HTTPException(status_code=403, detail='今日这个客户的数据已存在,不能重复添加!')
            cursor.execute(
                "INSERT INTO work_customer_index (create_time,join_time,update_time,customer_id,"
                "remain,interest,crights,note) VALUES (%(create_time)s,%(join_time)s,%(update_time)s,"
                "%(customer_id)s,%(remain)s,%(interest)s,%(crights)s,%(note)s);",
                index_content
            )
        else:
            raise HTTPException(status_code=403, detail='需本人客户才能进行添加记录!')
    return {'message': '添加成功!'}


@income_api.get('/customer/index/detail/')  # 查询一个客户的权益记录明细
async def get_customer_index_detail(customer_id: int = Query(...)):
    # 查询
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT cstindex.*,csttb.customer_name,csttb.account "
            "FROM work_customer_index AS cstindex "
            "INNER JOIN work_customer AS csttb ON cstindex.customer_id=csttb.id "
            "WHERE csttb.id=%s "
            "ORDER BY cstindex.create_time DESC;",
            (customer_id, )
        )
        indexes = cursor.fetchall()
    indexes = list(map(handle_customer_item, indexes))
    customer_name = indexes[0]['customer_name'] if indexes else ''
    return {'message': '查询成功!', 'indexes': indexes, 'customer_name': customer_name}


@income_api.put('/customer/index/modify/{index_id}/')  # 编辑一条客户权益
async def modify_customer_index(index_id: int, body_item: ModifyCustomerIndexItem = Body(...)):
    user_id, is_admin = validate_operate_user(body_item.user_token, 'revenue')
    # 是admin能修改,非admin只能修改自己的客户记录
    # 找出该记录所属的customer,验证customer的归属
    with DBWorker() as (_, cursor):
        if not is_admin:
            cursor.execute("SELECT id,customer_id FROM work_customer_index WHERE id=%s;", (body_item.index_id, ))
            index_obj = cursor.fetchone()
            if not index_obj:
                raise HTTPException(status_code=400, detail='记录不存在!')
            cursor.execute("SELECT id FROM work_customer WHERE id=%s AND author_id=%s;",
                           (index_obj['customer_id'], user_id))
            customer_obj = cursor.fetchone()
            if not customer_obj:
                raise HTTPException(status_code=400, detail='客户不存在!')
        # 进行修改
        cursor.execute(
            "UPDATE work_customer_index SET remain=%s,interest=%s,crights=%s "
            "WHERE id=%s;",
            (body_item.remain, body_item.interest, body_item.crights, index_id)
        )
    return {'message': '修改成功!'}


@income_api.delete('/customer/index/remove/{index_id}/')  # 删除一条客户权益
async def remove_customer_index(index_id: int, user_token: str = Query(...)):
    user_id, is_admin = validate_operate_user(user_token, 'revenue')
    # 是admin能删除,非admin只能删除自己的客户记录
    # 找出该记录所属的customer,验证customer的归属
    with DBWorker() as (_, cursor):
        if not is_admin:
            cursor.execute("SELECT id,customer_id FROM work_customer_index WHERE id=%s;", (index_id,))
            index_obj = cursor.fetchone()
            if not index_obj:
                raise HTTPException(status_code=400, detail='记录不存在!')
            cursor.execute("SELECT id FROM work_customer WHERE id=%s AND author_id=%s;",
                           (index_obj['customer_id'], user_id))
            customer_obj = cursor.fetchone()
            if not customer_obj:
                raise HTTPException(status_code=400, detail='客户不存在!')
        # 进行删除
        cursor.execute(
            "DELETE FROM work_customer_index WHERE id=%s LIMIT 1;", (index_id, )
        )
    return {'message': '删除成功!'}
