# _*_ coding:utf-8 _*_
# @File  : special_article.py
# @Time  : 2021-01-18 13:35
# @Author: zizle

# 迁移专题研究的数据库

from db import DBWorker

SCORES = {
    'A': 5,
    'B': 4,
    'C': 3,
}


def create_special_article_table():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `work_monographic` ("
            "`id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
            "`create_time` INT NOT NULL COMMENT '创建日期',"
            "`join_time` INT NOT NULL COMMENT '上传时间',"
            "`update_time` INT NOT NULL COMMENT '更新日期',"
            "`author_id` INT NOT NULL COMMENT '用户ID',"
            "`title` VARCHAR(128) NOT NULL COMMENT '文章标题',"
            "`words` INT NOT NULL DEFAULT 0 COMMENT '字数',"
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
        cursor.execute(
            "SELECT * "
            "FROM monographic;"
        )
        articles = cursor.fetchall()
        for item in articles:
            create_time = item['create_time']
            item['create_time'] = int(item['custom_time'].timestamp())
            item['join_time'] = int(create_time.timestamp())
            item['update_time'] = int(create_time.timestamp())
            item['annex_url'] = item['annex_url'].replace('fileStore', 'Annexes')
            item['score'] = SCORES.get(item['level'], 3)
        # 保存
        cursor.executemany(
            "INSERT INTO work_monographic (create_time,join_time,update_time,author_id,title,"
            "words,partner,score,annex,annex_url,is_publish)"
            "VALUES (%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,%(title)s,"
            "%(words)s,%(partner)s,%(score)s,%(annex)s,%(annex_url)s,%(is_publish)s);",
            articles
        )


if __name__ == '__main__':
    create_special_article_table()
    migrate_article()
