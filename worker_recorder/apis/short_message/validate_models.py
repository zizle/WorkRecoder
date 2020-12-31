# _*_ coding:utf-8 _*_
# @File  : validate_models.py
# @Time  : 2020-12-30 18:15
# @Author: zizle

from pydantic import BaseModel


# 管理员post请求短讯通数据的body参数
class AuditMsgBodyItem(BaseModel):
    page: int
    page_size: int
    user_token: str
    req_staff: list
    start_date: str
    end_date: str
    keyword: str


# 管理员批注短讯通的body参数
class AuditMessageItem(BaseModel):
    user_token: str
    audit_mind: int
