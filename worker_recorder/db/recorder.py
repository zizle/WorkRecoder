# _*_ coding:utf-8 _*_
# @File  : recorder.py
# @Time  : 2020-12-28 10:45
# @Author: zizle

import MySQLdb

from .db_pool import pool


class DBWorker(object):
    def __init__(self):
        print('连接池的ID:', id(pool))
        # 从连接池取得一个连接
        self.conn = pool.connection()
        # 获取连接游标
        self.cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)

    def __enter__(self):
        self.conn.begin()
        return self.conn, self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()
        # 将连接放回线程池
        self.cursor.close()
        print('游标关闭')
        self.conn.close()
        print('连接放回')


