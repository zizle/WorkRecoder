# _*_ coding:utf-8 _*_
# @File  : validate_models.py
# @Time  : 2021-01-11 08:50
# @Author: zizle

import json
import datetime
from fastapi import Form, HTTPException
from pydantic import BaseModel, ValidationError, validator


class AbnormalWorkAddItem(BaseModel):
    user_token: str
    create_time: str
    title: str
    task_type: int
    sponsor: str
    applicant: str
    phone: str
    swiss_coin: int
    allowance: float
    partner: str
    note: str

    @validator('create_time')
    def validate_create_time(cls, value):
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValidationError:
            raise ValidationError('create_date can not format `%Y-%m-%d`')
        return value


# 查询非常规工作的post-body参数
class QueryAbnormalItem(BaseModel):
    user_token: str
    start_date: str
    end_date: str
    # page: int = 1
    # page_size: int = 50
    keyword: str
    req_staff: list = []
    is_audit: int = 0


class AbnormalModifyBodyItem(BaseModel):
    user_token: str
    abnormal_id: int
    title: str
    sponsor: str
    applicant: str
    phone: str
    swiss_coin: str
    partner: str
    score: int
    note: str
    allowance: int


class AuditAbnormalItem(BaseModel):
    user_token: str
    abnormal_id: int
    score: int
    is_examined: int


def get_abnormal_content_item(body_data: str = Form(...)):
    try:
        body_content = json.loads(body_data)
        item = AbnormalWorkAddItem(**body_content)
    except json.decoder.JSONDecodeError:
        raise HTTPException(status_code=400, detail='body_data can not parse,it must be JSON string.')
    except ValidationError as e:
        print(e)
        raise HTTPException(status_code=422, detail=str(e))
    return item


def get_abnormal_modify_item(body_data: str = Form(...)):
    try:
        body_content = json.loads(body_data)
        item = AbnormalModifyBodyItem(**body_content)
    except json.decoder.JSONDecodeError:
        raise HTTPException(status_code=400, detail='body_data can not parse,it must be JSON string.')
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return item

