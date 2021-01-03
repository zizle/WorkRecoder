# _*_ coding:utf-8 _*_

import os
import platform

APP_DIR = os.path.dirname(os.path.abspath(__file__))  # 项目根路径
SECRET_KEY = "c7jgb1k2xzfq*3odq5my-vts^+cv+p7suw+(_5#va%f0=tt5mp"

STATICS_STORAGE = "E:/STATICS_WORKRECORDER/" if platform.system() == 'Windows' else '/Users/zizle/Desktop/WORKRECODER/STATICS_WORKRECORDER'

print(STATICS_STORAGE)

APP_HOST = "http://127.0.0.1:8000/"

TOKEN_EXPIRES = 3600  # seconds

DATABASE = {
    'worker_db': {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'mysql',
        'db_name': 'worker_recorder'
    }
}
