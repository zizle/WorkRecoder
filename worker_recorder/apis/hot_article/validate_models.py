# _*_ coding:utf-8 _*_
# @File  : validate_models.py
# @Time  : 2021-01-11 08:50
# @Author: zizle

import json
import datetime
from fastapi import Form, HTTPException
from pydantic import BaseModel, ValidationError, validator


class ArticleAddBodyItem(BaseModel):
    user_token: str
    create_time: str
    title: str
    media_name: str
    rough_type: str
    words: int
    checker: str
    allowance: int
    partner: str
    score: int
    note: str
    is_publish: int

    @validator('create_time')
    def validate_create_time(cls, value):
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValidationError:
            raise ValidationError('create_date can not format `%Y-%m-%d`')
        return value


# 查询投资方案的post-body参数
class QueryArticleItem(BaseModel):
    user_token: str
    start_date: str
    end_date: str
    # page: int = 1
    # page_size: int = 50
    keyword: str
    req_staff: list = []
    is_audit: int = 0


class ArticleModifyBodyItem(BaseModel):
    user_token: str
    article_id: int
    media_name: str
    checker: str
    allowance: int
    partner: str
    score: int
    note: str
    is_publish: int


def get_article_content_item(body_data: str = Form(...)):
    try:
        body_content = json.loads(body_data)
        item = ArticleAddBodyItem(**body_content)
    except json.decoder.JSONDecodeError:
        raise HTTPException(status_code=400, detail='body_data can not parse,it must be JSON string.')
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return item


def get_article_modify_item(body_data: str = Form(...)):
    try:
        body_content = json.loads(body_data)
        item = ArticleModifyBodyItem(**body_content)
    except json.decoder.JSONDecodeError:
        raise HTTPException(status_code=400, detail='body_data can not parse,it must be JSON string.')
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return item

