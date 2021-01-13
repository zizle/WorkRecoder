# _*_ coding:utf-8 _*_
# @File  : income_point.py
# @Time  : 2021-01-13 10:49
# @Author: zizle

# 建表和迁移客户和指标记录数据

from db import DBWorker


def create_income_point_table():
    with DBWorker() as (_, cursor):
        # 客户表
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `work_customer` ("
            "`id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
            "`create_time` INT NOT NULL COMMENT '开发日期',"
            "`join_time` INT NOT NULL COMMENT '上传时间',"
            "`update_time` INT NOT NULL COMMENT '更新日期',"
            "`author_id` INT NOT NULL COMMENT '归属用户',"
            "`customer_name` VARCHAR(128) NOT NULL COMMENT '客户名称',"
            "`account` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '客户账号',"
            "`note` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '备注',"
            "`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效'"
            ") DEFAULT CHARSET='utf8mb4';"
        )
        # 客户指标数据表
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `work_customer_index` ("
            "`id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
            "`create_time` INT NOT NULL COMMENT '记录日期',"
            "`join_time` INT NOT NULL COMMENT '上传时间',"
            "`update_time` INT NOT NULL COMMENT '更新日期',"
            "`customer_id` INT NOT NULL COMMENT '归属客户',"
            "`remain` DECIMAL(11,2) NOT NULL  DEFAULT 0 COMMENT '留存',"
            "`interest` DECIMAL(11,2) NOT NULL  DEFAULT 0 COMMENT '利息',"
            "`crights` DECIMAL(11,2) NOT NULL DEFAULT 0 COMMENT '权益',"
            "`note` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '备注',"
            "`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效'"
            ") DEFAULT CHARSET='utf8mb4';"
        )


def migrate_tables():
    with DBWorker() as (_, cursor):
        # 1.迁移客户数据库
        cursor.execute("SELECT * FROM info_customer;")
        customers = cursor.fetchall()
        for item in customers:
            create_time = item['create_time']
            item['create_time'] = int(create_time.timestamp())
            item['join_time'] = int(create_time.timestamp())
            item['update_time'] = int(create_time.timestamp())
            item['author_id'] = item['belong_user']
            item['customer_name'] = item['name']

        # 入库
        cursor.executemany(
            "INSERT INTO work_customer (id,create_time,join_time,update_time,author_id,customer_name,"
            "account,note) VALUES (%(id)s,%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,"
            "%(customer_name)s,%(account)s,%(note)s);",
            customers
        )
        # 2.迁移权益数据库
        cursor.execute("SELECT * FROM customer_rights;")
        customer_rights = cursor.fetchall()
        for item in customer_rights:
            create_time = item['create_time']
            item['create_time'] = int(item['custom_time'].timestamp())
            item['join_time'] = int(create_time.timestamp())
            item['update_time'] = int(create_time.timestamp())
        # 入库
        cursor.executemany(
            "INSERT INTO work_customer_index (id,create_time,join_time,update_time,customer_id,remain,"
            "interest,crights,note) VALUES (%(id)s,%(create_time)s,%(join_time)s,%(update_time)s,%(customer_id)s,"
            "%(remain)s,%(interest)s,%(crights)s,%(note)s);",
            customer_rights
        )


if __name__ == '__main__':
    create_income_point_table()
    migrate_tables()
