# _*_ coding:utf-8 _*_
# @File  : user.py
# @Time  : 2020-12-28 15:58
# @Author: zizle

from worker_recorder.db import DBWorker


def create_user_table():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `user_user` ("
            "`id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
            "`join_time` INT NOT NULL COMMENT '加入日期',"
            "`update_time` INT NOT NULL COMMENT '最近登录',"
            "`username` VARCHAR(32) NOT NULL COMMENT '用户名',"
            "`fixed_code` VARCHAR(20) NOT NULL COMMENT '用户号',"
            "`password` VARCHAR(32) NOT NULL COMMENT 'hash密码',"
            "`phone` CHAR(11) NOT NULL UNIQUE COMMENT '手机号',"
            "`email` VARCHAR(64) DEFAULT '' COMMENT '邮箱',"
            "`organization` INT NOT NULL DEFAULT 0,"
            "`is_admin` BIT NOT NULL DEFAULT 0,"
            "`is_active` BIT NOT NULL DEFAULT 1"
            ") DEFAULT CHARSET='utf8';"
        )

def migrate_users():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT * FROM user_info;"
        )
        users = cursor.fetchall()
        for item in users:
            item['join_time'] = int(item['join_time'].timestamp())
            item['update_time'] = int(item['update_time'].timestamp())
            item['organization'] = item['org_id']
            item['username'] = item['name']
        # 保存
        cursor.executemany(
            "INSERT INTO user_user (id,join_time,update_time,username,fixed_code,password,phone,email,"
            "organization,is_admin,is_active)"
            "VALUES (%(id)s,%(join_time)s,%(update_time)s,%(username)s,%(fixed_code)s,%(password)s,%(phone)s,%(email)s,"
            "%(organization)s,%(is_admin)s,%(is_active)s);",
            users
        )


if __name__ == '__main__':
    # create_user_table()
    migrate_users()
