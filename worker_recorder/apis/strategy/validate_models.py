# _*_ coding:utf-8 _*_
# @File  : validate_models.py
# @Time  : 2021-01-06 16:23
# @Author: zizle

import datetime
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError, validator


class StrategyAddItem(BaseModel):
    user_token: str
    create_time: str
    content: str
    variety_en: str
    contract: str
    direction: str
    hands: float
    open_price: float
    close_price: float
    profit: float
    note: str

    @validator('user_token')
    def validate_user_token(cls, value):
        if not value:
            raise ValidationError('user_token is required!')
        return value

    @validator('create_time')
    def validate_create_time(cls, value):
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            raise ValidationError('create_time can not format `%Y-%m-%d`.')
        return value


