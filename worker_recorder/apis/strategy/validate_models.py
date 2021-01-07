# _*_ coding:utf-8 _*_
# @File  : validate_models.py
# @Time  : 2021-01-06 16:23
# @Author: zizle

import datetime
from pydantic import BaseModel, ValidationError, validator


# 手动添加一条策略验证
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
    is_running: int
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

    @validator('is_running')
    def validate_is_running(cls, value):
        if value not in [0, 1]:
            raise ValidationError('is_running must be `0` or `1`!')
        return value


# 查询年度策略的post-body参数
class QueryStrategyItem(BaseModel):
    user_token: str
    start_date: str
    end_date: str
    page: int = 1
    page_size: int = 50
    keyword: str
    req_staff: list = []
    is_audit: int = 0

    @validator('page_size')
    def validate_page_size(cls, value):
        if value > 2000:
            raise ValidationError('page_size too large!')
        return value

    @validator('page')
    def validate_page(cls, value):
        if value < 1:
            raise ValidationError('page must be >= 1 !')
        return value
