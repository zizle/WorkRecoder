# _*_ coding:utf-8 _*_
# @File  : constants.py
# @Time  : 2020-12-28 16:05
# @Author: zizle

""" 一些常量 """


# 人员部门组织
ORGANIZATIONS = {
    0: "其他",
    1: "宏观金融",
    2: "化工小组",
    3: "农产品组",
    4: "金属小组",
    5: "创新部门",
}


# 品种分类
VARIETY_GROUPS = {
    0: '其他',
    1: '金融股指',
    2: '农业产品',
    3: '能源化工',
    4: '金属产业'
}

# 交易所分类
EXCHANGES = {
    0: '其他',
    1: '中国金融期货交易所',
    2: '郑州商品交易所',
    3: '大连商品交易所',
    4: '上海期货交易所',
    5: '国际能源交易中心'
}


# 短讯通审核意见
MSG_AUDIT_MIND = {
    0: '正常',
    1: '编写有误',
    2: '敏感词汇',
    3: '遭遇投诉',
    4: '其他问题'
}

# 品种对应中文
VARIETY_CN = {
    'GZ': '股指',
    'GZQH': '国债',
    'MYRMB': '',
    'MYZS': '',
    'A': '豆一',
    'B': '豆二'
}