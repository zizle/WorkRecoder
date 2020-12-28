# _*_ coding:utf-8 _*_
# @File  : encryption.py
# @Time  : 2020-12-28 11:12
# @Author: zizle

import time
import hashlib
import random
import string
from jose import jwt, JWTError
from settings import SECRET_KEY, TOKEN_EXPIRES


def encrypt_password(password):
    hasher = hashlib.md5()
    hasher.update(password.encode('utf-8'))
    hasher.update(SECRET_KEY.encode('utf-8'))
    # print('输入密码hash后：', hasher.hexdigest())
    return hasher.hexdigest()


def generate_user_token(data: dict, expire_seconds: int = TOKEN_EXPIRES):
    """ 生成用户的token """
    to_encode = data.copy()
    expire = time.time() + expire_seconds
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encode_jwt


def decipher_user_token(token: str):
    """ 解密token """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms='HS256')
        user_id: int = payload.get("user_id")  # `user_code`与生成时的对应
        access: list = payload.get("access", [])
        if user_id is None:
            raise JWTError
    except JWTError:
        return None, None
    return user_id, access


def genetate_user_fixed_code():
    """ 生成用户的fixed_code """
    return 'User_' + ''.join(random.sample(string.ascii_letters, 10))


