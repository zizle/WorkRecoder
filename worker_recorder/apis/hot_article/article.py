# _*_ coding:utf-8 _*_
# @File  : article.py
# @Time  : 2021-01-12 16:00
# @Author: zizle

import os
import datetime
from fastapi import APIRouter, UploadFile, Form, Depends, Body, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from apis.tools import validate_operate_user, validate_date_range, filter_records
from utils.file_hands import get_file_paths
from db import DBWorker
from settings import APP_HOST, STATICS_STORAGE

from .validate_models import (ArticleAddBodyItem, get_article_content_item, QueryArticleItem,
                              ArticleModifyBodyItem, get_article_modify_item)

article_api = APIRouter()


def handle_article_item(item):
    item['create_time'] = datetime.datetime.fromtimestamp(item['create_time']).strftime('%Y-%m-%d')
    item['join_time'] = datetime.datetime.fromtimestamp(item['join_time']).strftime('%Y-%m-%d %H:%M:%S')
    item['update_time'] = datetime.datetime.fromtimestamp(item['update_time']).strftime('%Y-%m-%d %H:%M:%S')
    item['annex_url'] = APP_HOST + 'static/' + item['annex_url']
    return item


@article_api.post('/add/')  # 用户添加一条文章记录(可能含附件)
async def add_hot_article(annex_file: UploadFile = Form(None),
                          body_item: ArticleAddBodyItem = Depends(get_article_content_item)):
    # 验证用户
    user_id, is_audit = validate_operate_user(body_item.user_token, 'investment')
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
        save_path, sql_path = get_file_paths('ARTICLE', user_id, annex_file.filename)
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
            "INSERT INTO work_article (create_time,join_time,update_time,author_id,title,media_name,rough_type,"
            "words,checker,allowance,partner,score,note,annex,annex_url,"
            "is_publish) VALUES (%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,%(title)s,"
            "%(media_name)s,%(rough_type)s,%(words)s,%(checker)s,%(allowance)s,%(partner)s,%(score)s,"
            "%(note)s,%(annex)s,%(annex_url)s,%(is_publish)s);",
            body_content
        )
        if count < 1 and save_path and os.path.exists(save_path) and os.path.isfile(save_path):
            # 添加失败,移除文件
            os.remove(save_path)
    return {'message': '添加热点文章记录成功!'}


@article_api.post('/')  # 查询用户指定范围内的文章记录,并返回结果
async def get_hot_article(query_item: QueryArticleItem = Body(...)):
    # 验证用户
    audit = 'article' if query_item.is_audit else None
    user_id, is_audit = validate_operate_user(query_item.user_token, audit)
    start_timestamp, end_timestamp = validate_date_range(query_item.start_date, query_item.end_date)
    # 查询数据
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT artb.*,usertb.username "
            "FROM work_article AS artb "
            "INNER JOIN user_user AS usertb ON artb.author_id=usertb.id "
            "WHERE artb.create_time>%s AND artb.create_time<=%s AND IF(1=%s,TRUE,artb.author_id=%s) "
            "ORDER BY artb.create_time DESC;",
            (start_timestamp, end_timestamp, is_audit, user_id)
        )
        articles = cursor.fetchall()
    articles, _ = filter_records(
        is_audit, query_item.req_staff, query_item.keyword, 'title', articles, [])
    articles = list(map(handle_article_item, articles))
    return {'message': '获取投资方案成功!', 'articles': articles}


@article_api.put('/modify/{article_id}/')  # 用户修改一条文章记录信息
async def modify_investment(article_id: int,
                            annex_file: UploadFile = Form(None),
                            body_item: ArticleModifyBodyItem = Depends(get_article_modify_item)):
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
            "SELECT * FROM work_article WHERE id=%s AND IF(1=%s,TRUE,author_id=%s);",
            (article_id, is_audit, user_id)
        )
        article_obj = cursor.fetchone()
        if not article_obj:
            raise HTTPException(status_code=400, detail='investment item Not Found')
        # 有附件，删除原来的附件并保存现在的附件
        if annex_file:
            old_annex_url = os.path.join(STATICS_STORAGE, article_obj['annex_url'])
            save_path, sql_path = get_file_paths('ARTICLE', user_id, annex_file.filename)

            body_content['annex'] = annex_file.filename
            body_content['annex_url'] = sql_path
            cursor.execute(
                "UPDATE work_article SET title=%(title)s,media_name=%(media_name)s,checker=%(checker)s,"
                "allowance=%(allowance)s,partner=%(partner)s,score=%(score)s,note=%(note)s,"
                "is_publish=%(is_publish)s,annex=%(annex)s,annex_url=%(annex_url)s "
                "WHERE id=%(article_id)s AND IF(1=%(is_audit)s,TRUE,author_id=%(user_id)s)"
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
                "UPDATE work_article SET title=%(title)s,media_name=%(media_name)s,checker=%(checker)s,"
                "allowance=%(allowance)s,partner=%(partner)s,score=%(score)s,note=%(note)s,"
                "is_publish=%(is_publish)s "
                "WHERE id=%(article_id)s AND IF(1=%(is_audit)s,TRUE,author_id=%(user_id)s)"
                " LIMIT 1;",
                body_content
            )
    return {'message': '修改成功!'}


@article_api.delete('/remove/{article_id}/')  # 用户或管理者删除一条热点文章的记录
async def delete_investment_record(article_id: int, user_token: str = Query(...)):
    user_id, is_audit = validate_operate_user(user_token, 'admin')
    # 删除数据
    with DBWorker() as (_, cursor):
        cursor.execute('SELECT id,author_id,annex_url FROM work_article WHERE id=%s;', (article_id,))
        article_record = cursor.fetchone()
        if article_record:
            if is_audit != 1 and article_record['author_id'] != user_id:
                raise HTTPException(status_code=403, detail='不能删除他人的数据记录!')
            # 删除记录
            cursor.execute(
                "DELETE FROM work_article WHERE id=%s AND IF(1=%s,TRUE,author_id=%s) LIMIT 1;",
                (article_id, is_audit, user_id)
            )
            # 删除附件
            if article_record['annex_url']:
                annex_path = os.path.join(STATICS_STORAGE, article_record['annex_url'])
                if os.path.exists(annex_path) and os.path.isfile(annex_path):
                    os.remove(annex_path)
            return {'message': '删除成功!'}
        else:
            raise HTTPException(status_code=400, detail='数据不存在!')

