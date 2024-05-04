import time
import random
import uuid
import re
import json
import constant
from hashlib import md5
from log_config import log
from request import http, get_new_session


# 米游社版本与对应的salt，以及一些固定值
mysVersion = '2.67.1'
salt_K2 = 'yajbb9O8TgQYOW7JVZYfUJhXN7mAeZPE'
salt_6X = 't0qEgfub6cvueAPgR5m9aQWWVciEer7v'
client_type = '2'  # 1:ios 2:android
device_id = uuid.uuid4().__str__().upper()
bbs_app_id = 'bll8iq97cem8'


# 米游社API
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

url_FetchQrcode = 'https://hk4e-sdk.mihoyo.com/hk4e_cn/combo/panda/qrcode/fetch'
"""生成二维码"""

url_QueryQrcode = 'https://hk4e-sdk.mihoyo.com/hk4e_cn/combo/panda/qrcode/query'
"""查询二维码状态"""

url_GetSTokenByGameToken = 'https://api-takumi.mihoyo.com/account/ma-cn-session/app/getTokenByGameToken'
"""通过Game Token获取SToken"""


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


def get_bbs_nickname(uid: str) -> str:
    """获取米游社昵称"""
    resp = http.get(url=nicknameUrl.format(uid))
    data = resp.json()
    if data['retcode'] == 0:
        return data['data']['user_info']['nickname']
    else:
        log.error(f'米游社昵称获取失败，原因：{data}')
        raise RuntimeError


def fetch_qrcode(app_id: str):
    """生成二维码"""
    resp = http.post(url_FetchQrcode, json={'app_id': app_id, 'device': device_id})
    data = resp.json()
    if data['retcode'] == 0:
        url = data['data']['url']
        ticket = re.search(r'ticket=((\d|[a-f])+)', url).group(1)
        return url, ticket
    else:
        return None, data


def query_qrcode_status(app_id: str, ticket: str):
    """查询二维码扫描状态"""
    resp = http.post(url_QueryQrcode, json={'app_id': app_id, 'device': device_id, 'ticket': ticket})
    data = resp.json()
    if data['retcode'] == -106:
        return constant.QRCODE_EXPIRED, None
    data = data['data']
    if data['stat'] == constant.QRCODE_CONFIRMED:
        return constant.QRCODE_CONFIRMED, json.loads(data['payload']['raw'])
    return None, None


def get_stoken_by_game_token(uid: int, game_token: str):
    """通过Game Token获取SToken"""
    header = {
        'Host': 'api-takumi.mihoyo.com',
        'Referer': 'https://app.mihoyo.com',
        'Origin': 'https://api-takumi.mihoyo.com',
        'User-Agent': f'Mozilla/5.0 (Linux; Android 12; LIO-AN00 Build/TKQ1.220829.002; wv) AppleWebKit/537.36 '
                      f'(KHTML, like Gecko) Version/4.0 Chrome/103.0.5060.129 Mobile Safari/537.36 miHoYoBBS/{mysVersion}',
        'x-rpc-app_id': bbs_app_id
    }
    req = get_new_session()
    resp = req.post(url_GetSTokenByGameToken,
                    headers=header, json={'account_id': uid, 'game_token': game_token})
    data = resp.json()
    if data['retcode'] == 0:
        log.info('获取stoken和mid成功')
        return data['data']['token']['token'], data['data']['user_info']['mid']
    else:
        log.error(f'获取stoken和mid失败，原因：{data}')
        return None, None


def change_cookie_by_stoken_version(uid: str, stoken: str, mid: str):
    """
    根据stoken的版本来使用不同的cookie
    :return: v1：stoken+stuid，v2：stoken+mid
    """
    if stoken.startswith('v2_'):
        return {'stoken': stoken, 'mid': mid}
    return {'stoken': stoken, 'stuid': uid}
