# _*_ coding:utf-8 _*_
# @Time  : 2021-01-02 17:27
# @Author: zizle

from worker_recorder.db import DBWorker

SCORES = {
    'A': 5,
    'B': 4,
    'C': 3
}


def create_investment_table():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `work_investment` ("
            "`id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
            "`create_time` INT NOT NULL COMMENT '创建方案',"
            "`update_time` INT NOT NULL COMMENT '更新日期',"
            "`author_id` INT NOT NULL COMMENT '用户ID',"
            "`title` VARCHAR(128) NOT NULL COMMENT '方案标题',"
            "`variety_en` VARCHAR(32) NOT NULL COMMENT '品种',"
            "`contract` VARCHAR(16) NOT NULL COMMENT '合约',"
            "`direction` VARCHAR(2) NOT NULL COMMENT '方向',"
            "`build_price` DECIMAL(15,6) NOT NULL DEFAULT 0 COMMENT '实建均价',"
            "`out_price` DECIMAL(15,6) NOT NULL DEFAULT 0 COMMENT '实建均价',"
            "`build_hands` INT NOT NULL DEFAULT 0 COMMENT '实建手数',"
            "`cutloss_price` DECIMAL(15,6) NOT NULL DEFAULT 0 COMMENT '实建均价',"
            "`expire_time` INT NOT NULL COMMENT '有效期止',"
            "`profit` DECIMAL(15,6) NOT NULL DEFAULT 0 COMMENT '方案结果',"
            "`note` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '备注',"
            "`score` INT NOT NULL DEFAULT 1 COMMENT '评级得分',"
            "`annex` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '附件',"
            "`annex_url` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '附件URL',"
            "`is_publish` BIT NOT NULL DEFAULT 1 COMMENT '是否外发',"
            "`is_active` BIT NOT NULL DEFAULT 1 COMMENT '有效'"
            ") DEFAULT CHARSET='utf8';"
        )


def migrate_investment():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT investb.*,vartb.en_code "
            "FROM investment AS investb "
            "INNER JOIN variety AS vartb ON vartb.id=investb.variety_id;"
        )
        investment = cursor.fetchall()
        for item in investment:
            create_time = item['create_time']
            item['create_time'] = int(item['custom_time'].timestamp())
            item['update_time'] = int(create_time.timestamp())
            item['build_time'] = int(item['build_time'].timestamp())
            item['expire_time'] = int(item['expire_time'].timestamp())
            item['variety_en'] = item['en_code'].upper()
            item['score'] = SCORES.get(item['level'], 3),
            item['annex_url'] = item['annex_url'].replace('fileStore', 'annex')
        # 保存
        cursor.executemany(
            "INSERT INTO work_investment (id,create_time,update_time,author_id,title,variety_en,contract,direction,"
            "build_price,out_price,build_hands,cutloss_price,expire_time,profit,note,score,annex,annex_url,is_publish)"
            "VALUES (%(id)s,%(create_time)s,%(update_time)s,%(author_id)s,%(title)s,%(variety_en)s,%(contract)s,"
            "%(direction)s,%(build_price)s,%(out_price)s,%(build_hands)s,%(cutloss_price)s,%(expire_time)s,%(profit)s,"
            "%(note)s,%(score)s,%(annex)s,%(annex_url)s,%(is_publish)s);",
            investment
        )


if __name__ == '__main__':
    create_investment_table()
    migrate_investment()
