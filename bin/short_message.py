# _*_ coding:utf-8 _*_
# @File  : user.py
# @Time  : 2020-12-28 15:58
# @Author: zizle

from worker_recorder.db import DBWorker


def create_short_message_table():
    # create_time为产生日期, update_time为上传到系统或修改的日期
    with DBWorker() as (_, cursor):
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `work_short_message` ("
            "`id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
            "`create_time` INT NOT NULL COMMENT '创建时间',"
            "`join_time` INT NOT NULL COMMENT '上传时间',"
            "`update_time` INT NOT NULL COMMENT '更新时间',"
            "`author_id` INT NOT NULL COMMENT '创建者',"
            "`content` VARCHAR(1024) NOT NULL COMMENT '信息内容',"
            "`msg_type` VARCHAR(32) DEFAULT '' COMMENT '类别',"
            "`effects` VARCHAR(64) DEFAULT '' COMMENT '影响品种',"
            "`note` VARCHAR(128) DEFAULT '' COMMENT '备注',"
            "`audit_mind` INT NOT NULL DEFAULT 0 COMMENT '审核意见',"
            "`is_active` BIT NOT NULL DEFAULT 1"
            ") DEFAULT CHARSET='utf8';"
        )


def migrate_message():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT * FROM short_message;"
        )
        messages = cursor.fetchall()
        for item in messages:
            create_time = int(item['create_time'].timestamp())
            item['create_time'] = int(item['custom_time'].timestamp())
            item['join_time'] = create_time
            item['update_time'] = create_time
            item['effects'] = item['effect_variety']
        # 保存
        cursor.executemany(
            "INSERT INTO work_short_message (id,create_time,join_time,update_time,author_id,"
            "content,msg_type,effects,note)"
            "VALUES (%(id)s,%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,%(content)s,"
            "%(msg_type)s,%(effects)s,%(note)s);",
            messages
        )


if __name__ == '__main__':
    create_short_message_table()
    migrate_message()
