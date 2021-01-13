# _*_ coding:utf-8 _*_
# @File  : validate_models.py
# @Time  : 2021-01-13 11:14
# @Author: zizle
import json
import datetime
from fastapi import Form, HTTPException
from pydantic import BaseModel, validator, ValidationError


# 添加客户的验证模型
class AddCustomerItem(BaseModel):
    user_token: str
    customer_name: str
    account: str
    note: str = ''


# 添加客户指标的验证模型
class AddCustomerIndexItem(BaseModel):
    user_token: str
    customer_id: int
    create_time: str
    remain: float
    interest: float
    crights: float
    note: str = ''

    @validator('create_time')
    def validate_create_time(cls, value):
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValidationError:
            raise ValidationError('create_date can not format `%Y-%m-%d`')
        return value


class ModifyCustomerIndexItem(BaseModel):
    user_token: str
    index_id: int
    remain: float
    interest: float
    crights: float
    note: str = ''


def get_modify_index_item(body_data: str = Form(...)):
    try:
        body_content = json.loads(body_data)
        item = ModifyCustomerIndexItem(**body_content)
    except json.decoder.JSONDecodeError:
        raise HTTPException(status_code=400, detail='body_data can not parse,it must be JSON string.')
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return item
