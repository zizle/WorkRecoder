# _*_ coding:utf-8 _*_
# @File  : file_hands.py
# @Time  : 2020-12-29 14:17
# @Author: zizle

# 处理文件的方法

import os
import numpy as np
import datetime
import random
import string
from settings import STATICS_STORAGE


# 转换日期列
def date_column_converter(source_datetime):
    if isinstance(source_datetime, datetime.datetime):
        return int(source_datetime.timestamp())
    else:
        return np.nan


def generate_unique_filename(file_folder, filename, suffix):
    filepath = os.path.join(file_folder, "{}{}".format(filename, suffix))
    abs_filepath = os.path.join(STATICS_STORAGE, filepath)
    if os.path.exists(abs_filepath):
        new_filename_suffix = ''.join(random.sample(string.ascii_letters, 6))
        new_filename = "{}_{}".format(filename, new_filename_suffix)
        return generate_unique_filename(file_folder, new_filename, suffix)
    else:
        return file_folder, filename, suffix


# 生成文件保存的绝对路径和SQL路径
def get_file_paths(module_name, user_id, filename):
    # 保存附件到指定文件夹
    date_folder = datetime.datetime.today().strftime('%Y%m')
    # 创建文件保存所在的路径
    save_folder = "Annexes/{}/{}/{}/".format(module_name, user_id, date_folder)
    abs_folder = os.path.join(STATICS_STORAGE, save_folder)
    if not os.path.exists(abs_folder):
        os.makedirs(abs_folder)
    pre_filename, file_suffix = os.path.splitext(filename)
    # 检测文件绝对路径名称是否存在,存在则需生成新的文件名，否则文件会被覆盖而使数据错误
    save_folder, new_filename, suffix = generate_unique_filename(save_folder, pre_filename, file_suffix)
    print('save_folder:', save_folder)
    print('new_filename:', new_filename)
    print('suffix:', suffix)
    filename_saved = "{}{}".format(new_filename, suffix)
    save_path = os.path.join(abs_folder, filename_saved)
    sql_path = os.path.join(save_folder, filename_saved)
    return save_path, sql_path


