import json
import time
import random
from hashlib import md5
from log_config import log

import requests

# 米游社版本及对应的salt
mysVersion = '2.34.1'
salt_K2 = 'z8DRIUjNDT7IT5IZXvrUAxyupA1peND9'  # 米游社2.34.1版本安卓客户端salt值
salt_6X = 't0qEgfub6cvueAPgR5m9aQWWVciEer7v'  # 这个给签到用
client_type = '2'  # 1:ios 2:android


# URL
stokenUrl = 'https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket?login_ticket={}&token_types=3&uid={}'
"""获取stoken URL"""

nicknameUrl = 'https://bbs-api.miyoushe.com/user/api/getUserFullInfo?uid={}'
"""获取米游社昵称 URL"""

verifyUrl = 'https://api-takumi.mihoyo.com/auth/api/getCookieAccountInfoBySToken'
"""验证stoken有效性 URL"""

signUrl = 'https://bbs-api.mihoyo.com/apihub/app/api/signIn'
"""频道打卡 URL"""

listUrl = 'https://bbs-api.mihoyo.com/post/api/getForumPostList?forum_id={}&is_good=false&is_hot=false&page_size=20&sort_type=1'
"""获取帖子列表 URL"""

detailUrl = 'https://bbs-api.mihoyo.com/post/api/getPostFull?post_id={}'
"""浏览帖子 URL"""

shareUrl = 'https://bbs-api.mihoyo.com/apihub/api/getShareConf?entity_id={}&entity_type=1'
"""分享帖子 URL"""

voteUrl = 'https://bbs-api.mihoyo.com/apihub/sapi/upvotePost'
"""点赞帖子 URL"""


# 米游社 频道-板块 ID对照表
channelList = [
    {
        'id': '1',
        'forumId': '1',  # 甲板
        'name': '崩坏3',
        'url': 'https://bbs.mihoyo.com/bh3/'
    },
    {
        'id': '2',
        'forumId': '26',  # 酒馆
        'name': '原神',
        'url': 'https://bbs.mihoyo.com/ys/'
    },
    {
        'id': '3',
        'forumId': '30',  # 学园
        'name': '崩坏学园2',
        'url': 'https://bbs.mihoyo.com/bh2/'
    },
    {
        'id': '4',
        'forumId': '37',  # 律所
        'name': '未定事件簿',
        'url': 'https://bbs.mihoyo.com/wd/'
    },
    {
        'id': '5',
        'forumId': '35',  # ACG
        'name': '大别野',
        'url': 'https://bbs.mihoyo.com/dby/'
    },
    {
        'id': '6',
        'forumId': '52',  # 候车室
        'name': '崩坏：星穹铁道',
        'url': 'https://bbs.mihoyo.com/sr/'
    },
    {
        'id': '8',
        'forumId': '57',  # 咖啡馆
        'name': '绝区零',
        'url': 'https://bbs.mihoyo.com/zzz/'
    }
]
"""
米游社 频道-板块 ID对照表：
    id：频道id
    forumId: 频道中有打卡按钮的版块id
"""


##########################################################################################################


def random_str(num):
    """生成指定位数的随机字符串"""
    letters_and_numbers = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.choices(letters_and_numbers, k=num))


def get_DS1():
    """DS1算法"""
    salt = salt_K2
    t = int(time.time())
    r = random_str(6)
    main = f'salt={salt}&t={t}&r={r}'
    ds = md5(main.encode(encoding='UTF-8')).hexdigest()
    return f'{t},{r},{ds}'


def get_DS2(body: str = '', query: str = '') -> str:
    """DS2算法"""
    salt = salt_6X
    t = int(time.time())
    r = random.randint(100001, 200000)
    main = f'salt={salt}&t={t}&r={r}&b={body}&q={query}'
    ds = md5(main.encode(encoding='UTF-8')).hexdigest()
    return f'{t},{r},{ds}'


def get_Nickname(stuid: str) -> str:
    """获取米游社昵称"""
    res = requests.get(url=nicknameUrl.format(stuid))
    data = json.loads(res.text.encode('utf-8'))
    if data['retcode'] == 0:
        return data['data']['user_info']['nickname']
    else:
        log.error(f'米游社昵称获取失败，原因：{data["message"]}')
        raise RuntimeError


def print_blank_line():
    """打印空行，用于日志信息间的分隔

    [修复] 日志信息会和相邻的print/input语句显示在同一行的问题
    [优化] 不同函数/方法、每次循环打印的日志间空一行，避免密密麻麻连成一片很难看
    """
    time.sleep(0.5)
    print()
    time.sleep(0.5)
