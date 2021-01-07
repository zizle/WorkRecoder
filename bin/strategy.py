# _*_ coding:utf-8 _*_
# @File  : user.py
# @Time  : 2021-01-02 16:34
# @Author: zizle

from worker_recorder.db import DBWorker


def create_strategy_table():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `work_strategy` ("
            "`id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',"
            "`create_time` INT NOT NULL COMMENT '策略日期',"
            "`join_time` INT NOT NULL COMMENT '上传时间',"
            "`update_time` INT NOT NULL COMMENT '更新时间',"
            "`author_id` INT NOT NULL COMMENT '用户ID',"
            "`content` VARCHAR(2048) NOT NULL COMMENT '策略内容',"
            "`variety_en` VARCHAR(32) NOT NULL COMMENT '品种',"
            "`contract` VARCHAR(16) NOT NULL COMMENT '合约',"
            "`direction` VARCHAR(2) NOT NULL COMMENT '方向',"
            "`hands` INT NOT NULL DEFAULT 0 COMMENT '手数',"
            "`open_price` DECIMAL(15,6) NOT NULL DEFAULT 0 COMMENT '策略开仓',"
            "`close_price` DECIMAL(15,6) NOT NULL DEFAULT 0 COMMENT '策略平仓',"
            "`profit` DECIMAL(15,6) NOT NULL DEFAULT 0 COMMENT '策略平仓',"
            "`note` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '备注',"
            "`is_active` BIT NOT NULL DEFAULT 1,"
            "`is_edit` BIT NOT NULL DEFAULT 1"
            ") DEFAULT CHARSET='utf8';"
        )


def migrate_strategy():
    with DBWorker() as (_, cursor):
        cursor.execute(
            "SELECT stratb.id,stratb.create_time,stratb.custom_time,stratb.author_id,"
            "stratb.content,stratb.variety_id,vartb.en_code,stratb.contract,stratb.direction,"
            "stratb.hands,stratb.open_position,stratb.close_position,stratb.profit,stratb.note "
            "FROM investrategy AS stratb "
            "INNER JOIN variety AS vartb ON vartb.id=stratb.variety_id;"
        )
        strategy = cursor.fetchall()
        for item in strategy:
            create_time = item['create_time']
            item['create_time'] = int(item['custom_time'].timestamp())
            item['update_time'] = int(create_time.timestamp())
            item['join_time'] = int(create_time.timestamp())
            item['open_price'] = item['open_position']
            item['close_price'] = item['close_position']
            item['variety_en'] = item['en_code'].upper()
        # 保存
        cursor.executemany(
            "INSERT INTO work_strategy (id,create_time,join_time,update_time,author_id,content,variety_en,contract,"
            "direction,hands,open_price,close_price,profit,note)"
            "VALUES (%(id)s,%(create_time)s,%(join_time)s,%(update_time)s,%(author_id)s,%(content)s,%(variety_en)s,"
            "%(contract)s,%(direction)s,%(hands)s,%(open_price)s,%(close_price)s,%(profit)s,%(note)s);",
            strategy
        )


if __name__ == '__main__':
    create_strategy_table()
    migrate_strategy()
