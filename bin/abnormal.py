# _*_ coding:utf-8 _*_
# Author: zizle
# Created: 2021-01-02 18:42
# ---------------------------

# _*_ coding:utf-8 _*_
# @Time  : 2021-01-02 17:27
# @Author: zizle

from worker_recorder.db import DBWorker


def create_abnormal_table():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `work_abnormal` ("
            "`id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
            "`create_time` INT NOT NULL COMMENT '创建方案',"
            "`join_time` INT NOT NULL COMMENT '上传时间',"
            "`update_time` INT NOT NULL COMMENT '更新日期',"
            "`author_id` INT NOT NULL COMMENT '用户ID',"
            "`title` VARCHAR(128) NOT NULL COMMENT '标题',"
            "`task_type` INT NOT NULL DEFAULT 0 COMMENT '任务类型',"
            "`sponsor` VARCHAR(32) NOT NULL DEFAULT '' COMMENT '主办方',"
            "`applicant` VARCHAR(32) NOT NULL DEFAULT '' COMMENT '申请者',"
            "`phone` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '联系电话',"
            "`swiss_coin` INT NOT NULL DEFAULT 0 COMMENT '瑞币',"
            "`allowance` DECIMAL(15,6) NOT NULL DEFAULT 0 COMMENT '收入补贴',"
            "`partner` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '合作者',"
            "`note` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '备注',"
            "`score` INT NOT NULL DEFAULT 1 COMMENT '评级得分',"
            "`annex` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '附件',"
            "`annex_url` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '附件URL',"
            "`is_examined` BIT NOT NULL DEFAULT 1 COMMENT '审核状态',"
            "`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效'"
            ") DEFAULT CHARSET='utf8mb4';"
        )


def migrate_abnormal():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT * FROM abnormal_work;"
        )
        abnormal = cursor.fetchall()
        for item in abnormal:
            create_time = item['create_time']
            item['create_time'] = int(item['custom_time'].timestamp())
            item['update_time'] = int(create_time.timestamp())
            item['join_time'] = int(create_time.timestamp())
            item['score'] = 3,
            item['annex_url'] = item['annex_url'].replace('fileStore', 'Annexes')
            item['phone'] = item['tel_number']
        # 保存
        cursor.executemany(
            "INSERT INTO work_abnormal (id,create_time,join_time,update_time,author_id,title,task_type,sponsor,"
            "applicant,phone,swiss_coin,allowance,partner,note,score,annex,annex_url,is_examined)"
            "VALUES (%(id)s,%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,%(title)s,%(task_type)s,"
            "%(sponsor)s,%(applicant)s,%(phone)s,%(swiss_coin)s,%(allowance)s,%(partner)s,"
            "%(note)s,%(score)s,%(annex)s,%(annex_url)s,%(is_examined)s);",
            abnormal
        )


if __name__ == '__main__':
    create_abnormal_table()
    migrate_abnormal()
