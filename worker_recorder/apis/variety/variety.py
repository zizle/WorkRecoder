# _*_ coding:utf-8 _*_

# 品种的API
# 1. 添加一个品种
# 2. 获取品种列表


from fastapi import APIRouter

variety_api = APIRouter()


@variety_api.get('/all/')  # 获取全部的品种,以交易代码排序
async def get_all_variety():
    return {'message': '获取品种成功!', 'varieties': [
        {'id': 1, 'variety': 'xxA', 'en': 'A'},
        {'id': 2, 'variety': 'xxB', 'en': 'B'},
    ]}




