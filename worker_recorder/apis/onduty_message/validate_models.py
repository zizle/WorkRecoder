# _*_ coding:utf-8 _*_
# @File  : validate_models.py
# @Time  : 2021-01-13 08:22
# @Author: zizle
import datetime
from pydantic import BaseModel, validator, ValidationError


# 查询值班信息post请求的body参数
class QueryMsgBodyItem(BaseModel):
    user_token: str
    start_date: str
    end_date: str
    page: int
    page_size: int
    keyword: str
    req_staff: list = []
    is_audit: int = 0


# 批量删除本次上传的值班信息body参数
class JoinTimeDelMsgItem(BaseModel):
    user_token: str
    join_time: int

# 用户添加一条值班信息的body
class AddOndutyMsgItem(BaseModel):
    user_token: str
    create_time: str
    content: str
    note: str

    @validator('create_time')
    def validate_create_time(cls, value):
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            raise ValidationError('create_time can not format `%Y-%m-%d`.')
        return value
