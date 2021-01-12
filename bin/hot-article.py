# _*_ coding:utf-8 _*_
# @File  : hot-article.py
# @Time  : 2021-01-12 15:27
# @Author: zizle

# 迁移专题研究和文章发表的数据库内容

from db import DBWorker

SCORES = {
    'A': 5,
    'B': 4,
    'C': 3,
}


def create_hot_article_table():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `work_article` ("
            "`id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
            "`create_time` INT NOT NULL COMMENT '创建方案',"
            "`join_time` INT NOT NULL COMMENT '上传时间',"
            "`update_time` INT NOT NULL COMMENT '更新日期',"
            "`author_id` INT NOT NULL COMMENT '用户ID',"
            "`title` VARCHAR(128) NOT NULL COMMENT '文章标题',"
            "`media_name` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '媒体名称',"
            "`rough_type` VARCHAR(32) NOT NULL DEFAULT '' COMMENT '稿件形式',"
            "`words` INT NOT NULL DEFAULT 0 COMMENT '字数',"
            "`checker` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '审核人',"
            "`allowance` INT NOT NULL DEFAULT 0 COMMENT '收入奖励',"
            "`partner` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '合作者',"
            "`score` INT NOT NULL DEFAULT 1 COMMENT '评级得分',"
            "`annex` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '附件',"
            "`annex_url` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '附件URL',"
            "`note` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '备注',"
            "`is_publish` BIT NOT NULL DEFAULT 1 COMMENT '是否外发',"
            "`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效'"
            ") DEFAULT CHARSET='utf8mb4';"
        )


def migrate_article():
    with DBWorker() as (_, cursor):
        # 1 迁移专题研究的内容(独立一个表，不作迁移了)
        # cursor.execute(
        #     "SELECT mtb.* "
        #     "FROM monographic AS mtb ;"
        # )
        # monographic = cursor.fetchall()
        # for item in monographic:
        #     create_time = item['create_time']
        #     item['create_time'] = int(item['custom_time'].timestamp())
        #     item['join_time'] = int(create_time.timestamp())
        #     item['update_time'] = int(create_time.timestamp())
        #     item['score'] = SCORES.get(item['level'], 3),
        #     item['annex_url'] = item['annex_url'].replace('fileStore', 'Annexes')
        #     item['allowance'] = 0
        #     item['media_name'] = ''
        #     item['rough_type'] = ''
        #     item['checker'] = ''

        cursor.execute(
            "SELECT * "
            "FROM article_publish;"
        )
        articles = cursor.fetchall()
        for item in articles:
            create_time = item['create_time']
            item['create_time'] = int(item['custom_time'].timestamp())
            item['join_time'] = int(create_time.timestamp())
            item['update_time'] = int(create_time.timestamp())
            item['annex_url'] = item['annex_url'].replace('fileStore', 'Annexes')
            item['score'] = 5
            item['is_publish'] = 0
        # 保存
        cursor.executemany(
            "INSERT INTO work_article (create_time,join_time,update_time,author_id,title,media_name,rough_type,"
            "words,checker,allowance,partner,score,annex,annex_url,is_publish)"
            "VALUES (%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,%(title)s,%(media_name)s,"
            "%(rough_type)s,%(words)s,%(checker)s,%(allowance)s,%(partner)s,%(score)s,"
            "%(annex)s,%(annex_url)s,%(is_publish)s);",
            articles
        )


if __name__ == '__main__':
    create_hot_article_table()
    migrate_article()
