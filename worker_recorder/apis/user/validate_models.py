# _*_ coding:utf-8 _*_

from pydantic import BaseModel


class UserLoginItem(BaseModel):
    username: str
    password: str
