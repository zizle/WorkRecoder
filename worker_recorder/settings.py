# _*_ coding:utf-8 _*_

import os
import platform

"""
# 各模块的权限验证字符串
1. 短讯通(short_message):  short_message
2. 投顾策略(strategy):     strategy
3. 投资方案(investment):   investment
4. 非常规工作(abnormal):   abnormal_work
5. 收入指标(income_point): revenue
6. 热点文章(hot_article):  article
"""


APP_DIR = os.path.dirname(os.path.abspath(__file__))  # 项目根路径
SECRET_KEY = "c7jgb1k2xzfq*3odq5my-vts^+cv+p7suw+(_5#va%f0=tt5mp"

STATICS_STORAGE = "E:/STATICS_WORKRECORDER/" if platform.system() == 'Windows' else '/Users/zizle/Desktop/WORKRECODER/STATICS_WORKRECORDER'

print(STATICS_STORAGE)

APP_HOST = "http://127.0.0.1:8000/"

TOKEN_EXPIRES = 36000  # seconds

DATABASE = {
    'worker_db': {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'mysql',
        'db_name': 'worker_recorder'
    }
}
