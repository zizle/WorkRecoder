# _*_ coding:utf-8 _*_
# @File  : onduty_message.py
# @Time  : 2021-01-13 08:07
# @Author: zizle

from worker_recorder.db import DBWorker


def create_onduty_message_table():
    # create_time为产生日期, join_time为上传到系统的日期, update_time为修改的日期
    with DBWorker() as (_, cursor):
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `work_onduty_message` ("
            "`id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
            "`create_time` INT NOT NULL COMMENT '创建时间',"
            "`join_time` INT NOT NULL COMMENT '上传时间',"
            "`update_time` INT NOT NULL COMMENT '更新时间',"
            "`author_id` INT NOT NULL COMMENT '创建者',"
            "`content` VARCHAR(1024) NOT NULL COMMENT '信息内容',"
            "`note` VARCHAR(128) DEFAULT '' COMMENT '备注',"
            "`is_active` BIT NOT NULL DEFAULT 1,"
            "`is_edit` BIT NOT NULL DEFAULT 1"
            ") DEFAULT CHARSET='utf8mb4';"
        )


def migrate_onduty_message():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT * FROM onduty_message;"
        )
        messages = cursor.fetchall()
        for item in messages:
            create_time = int(item['create_time'].timestamp())
            item['create_time'] = int(item['custom_time'].timestamp())
            item['join_time'] = create_time
            item['update_time'] = create_time
        # 保存
        cursor.executemany(
            "INSERT INTO work_onduty_message (id,create_time,join_time,update_time,author_id,"
            "content,note)"
            "VALUES (%(id)s,%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,%(content)s,%(note)s);",
            messages
        )


if __name__ == '__main__':
    create_onduty_message_table()
    migrate_onduty_message()
