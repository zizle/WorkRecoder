# _*_ coding:utf-8 _*_
# @File  : variety.py
# @Time  : 2020-12-29 08:21
# @Author: zizle
import datetime

from worker_recorder.db import DBWorker


def create_variety_table():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `variety_variety` ("
            "`id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
            "`create_time` INT NOT NULL COMMENT '创建日期',"
            "`update_time` INT NOT NULL COMMENT '最近修改',"
            "`variety_name` VARCHAR(8) NOT NULL COMMENT '品种名称',"
            "`variety_en` VARCHAR(8) NOT NULL COMMENT '交易代码',"
            "`group_id` INT NOT NULL COMMENT '分类',"
            "`exchange_id` INT NOT NULL COMMENT '交易所',"
            "`is_active` BIT NOT NULL DEFAULT 1,"
            "UNIQUE KEY `variety`(`variety_name`,`variety_en`)"
            ") DEFAULT CHARSET='utf8';"
        )


def migrate_variety():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT * FROM variety WHERE parent_id IS NOT NULL;"
        )
        varieties = cursor.fetchall()
        now_timestamp = int(datetime.datetime.now().timestamp())
        for item in varieties:
            item['create_time'] = now_timestamp
            item['update_time'] = now_timestamp
            item['variety_name'] = item['name']
            item['variety_en'] = item['en_code'].upper()
            item['group_id'] = item['parent_id']
            item['exchange_id'] = 0
        # 保存
        cursor.executemany(
            "INSERT INTO variety_variety (id,create_time,update_time,variety_name,variety_en,group_id,exchange_id) "
            "VALUES (%(id)s,%(create_time)s,%(update_time)s,%(variety_name)s,%(variety_en)s,%(group_id)s,"
            "%(exchange_id)s);",
            varieties
        )


if __name__ == '__main__':
    # create_variety_table()
    migrate_variety()
