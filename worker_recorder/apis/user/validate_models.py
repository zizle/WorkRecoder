# _*_ coding:utf-8 _*_

from pydantic import BaseModel


# 用户登录验证模型
class UserLoginItem(BaseModel):
    username: str
    password: str


# 添加用户验证模型
class UserAddedItem(BaseModel):
    operate_token: str
    username: str
    password: str
    phone: str
    organization: int
