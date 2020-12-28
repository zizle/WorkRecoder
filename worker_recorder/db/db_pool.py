# _*_ coding:utf-8 _*_
# @File  : db_pool.py
# @Time  : 2020-12-28 11:01
# @Author: zizle
import sys
import MySQLdb
from MySQLdb.converters import conversions
from MySQLdb.constants import FIELD_TYPE
from dbutils.pooled_db import PooledDB

from settings import DATABASE

db_params = DATABASE['worker_db']


def mysqlclient_converters():
    conversions[FIELD_TYPE.BIT] = lambda x: 1 if int.from_bytes(x, byteorder=sys.byteorder, signed=False) else 0
    return conversions


# MySQLdb连接池
pool = PooledDB(
    creator=MySQLdb, mincached=5, maxcached=10,
    host=db_params['host'], port=db_params['port'],
    user=db_params['user'], passwd=db_params['password'],
    db=db_params['db_name'], charset='utf8',
    conv=mysqlclient_converters()
)
