# _*_ coding:utf-8 _*_
# @File  : validate_models.py
# @Time  : 2020-12-30 18:15
# @Author: zizle

from pydantic import BaseModel


class AuditMsgBodyItem(BaseModel):
    page: int
    page_size: int
    user_token: str
    req_staff: list
    start_date: str
    end_date: str
