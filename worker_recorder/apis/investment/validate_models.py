# _*_ coding:utf-8 _*_
# @File  : validate_models.py
# @Time  : 2021-01-11 08:50
# @Author: zizle

import json
import datetime
from fastapi import Form, HTTPException
from pydantic import BaseModel, ValidationError, validator


class InvestmentAddBodyItem(BaseModel):
    user_token: str
    create_time: str
    title: str
    variety_en: str
    contract: str
    direction: str
    build_price: float
    build_hands: int
    out_price: float
    cutloss_price: float
    expire_time: str
    is_publish: int
    is_running: int
    score: int
    profit: float
    note: str

    @validator('create_time')
    def validate_create_time(cls, value):
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValidationError:
            raise ValidationError('create_date can not format `%Y-%m-%d`')
        return value

    @validator('expire_time')
    def validate_expire_time(cls, value):
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValidationError:
            raise ValidationError('expire_date can not format `%Y-%m-%d`')
        return value


# 查询投资方案的post-body参数
class QueryInvestmentItem(BaseModel):
    user_token: str
    start_date: str
    end_date: str
    # page: int = 1
    # page_size: int = 50
    keyword: str
    req_staff: list = []
    is_audit: int = 0


class InvestmentModifyBodyItem(BaseModel):
    user_token: str
    investment_id: int
    build_price: float
    build_hands: int
    out_price: float
    cutloss_price: float
    profit: float
    is_running: int
    score: int
    note: str


def get_investment_content_item(body_data: str = Form(...)):
    try:
        body_content = json.loads(body_data)
        item = InvestmentAddBodyItem(**body_content)
    except json.decoder.JSONDecodeError:
        raise HTTPException(status_code=400, detail='body_data can not parse,it must be JSON string.')
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return item


def get_investment_modify_item(body_data: str = Form(...)):
    try:
        body_content = json.loads(body_data)
        item = InvestmentModifyBodyItem(**body_content)
    except json.decoder.JSONDecodeError:
        raise HTTPException(status_code=400, detail='body_data can not parse,it must be JSON string.')
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return item

