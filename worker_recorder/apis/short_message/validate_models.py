# _*_ coding:utf-8 _*_
# @File  : validate_models.py
# @Time  : 2020-12-30 18:15
# @Author: zizle
import datetime
from pydantic import BaseModel, validator, ValidationError


# 查询短讯通post请求的body参数
class QueryMsgBodyItem(BaseModel):
    user_token: str
    start_date: str
    end_date: str
    page: int
    page_size: int
    keyword: str
    req_staff: list = []
    is_audit: int = 0


# 用户添加一条短讯通的body
class AddMsgBodyItem(BaseModel):
    user_token: str
    create_time: str
    content: str
    msg_type: str
    effects: str
    note: str

    @validator('create_time')
    def validate_create_time(cls, value):
        try:
            datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            raise ValidationError('create_time can not format `%Y-%m-%d`.')
        return value

# 管理员批注短讯通的body参数
class AuditMessageItem(BaseModel):
    user_token: str
    audit_mind: int


# 批量删除本次上传的短讯通body参数
class JoinTimeDelMsgItem(BaseModel):
    user_token: str
    join_time: int
