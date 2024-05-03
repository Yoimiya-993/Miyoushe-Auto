import json
import uuid
import time
import requests
import tools
import api
from json.decoder import JSONDecodeError
from log_config import log
from add_account import login_and_save


def load_user() -> list[dict]:
    """加载用户"""
    log.info('正在读取“user_info”文件...')
    try:
        with open('./data/user_info.json', 'r') as f:
            data = json.load(f)
            log.info(f'“user_info”文件读取完毕，共有{len(data)}个账号！')
            return data
    except FileNotFoundError:
        log.info('”user_info“文件不存在，请添加第一个账号...')
        users = login_and_save()
        log.info('账号添加成功！')
        return users
    except JSONDecodeError:
        log.error('“user_info”文件读取失败，请不要改动文件内容！若你无法还原，请删除该文件再重新添加保存过的账号')
        raise RuntimeError


class MiYouBiTask:
    """获取米游币

    由于每个人所玩的游戏都不一样，但【大别野】是大家都有的
    因此只需对【大别野】进行 打卡、浏览、点赞、分享
    """
    def __init__(self, user: dict):
        self.user = user
        self.headers = {
            'DS': api.get_DS1(),
            'x-rpc-client_type': api.client_type,
            'x-rpc-app_version': api.mysVersion,
            'x-rpc-sys_version': '12',
            'x-rpc-channel': 'miyousheluodi',
            'x-rpc-device_id': uuid.uuid4().__str__().upper(),
            'x-rpc-device_name': 'HONOR BKL-TL10',
            'x-rpc-device_model': 'BKL-TL10',
            'Referer': 'https://app.mihoyo.com',
            'Host': 'bbs-api.mihoyo.com',
            'User-Agent': 'okhttp/4.9.3'
        }
        self.da_bie_ye = api.channelList[4]
        self.nickname = api.get_nickname(user['stuid'])
        self.verifyStoken()
        self.articleList = self.getArticleList()

    def verifyStoken(self):
        """验证stoken的有效性"""
        log.info(f'正在验证用户 {self.nickname} 的登录状态...')
        resp = requests.get(url=api.verifyUrl, cookies=self.user)
        data = resp.json()
        if data['retcode'] == -100:
            log.error(f'{self.nickname} 的{data["message"]}')
            raise RuntimeError
        else:
            log.info(f'{self.nickname} 的登录状态正常！')

    def getArticleList(self) -> list[dict]:
        """预获取【大别野】的帖子以供 浏览、点赞、分享 使用

        根据 米游币任务：完成5次点赞，为最大值
        因此获取5条帖子
        """
        articles = []
        log.info('正在获取5个【大别野】的帖子...')
        resp = requests.get(url=api.listUrl.format(self.da_bie_ye['forumId']), headers=self.headers)
        data = resp.json()
        if data['retcode'] == 0:
            for i in range(5):
                articles.append({
                    'post_id': data['data']['list'][i]['post']['post_id'],
                    'subject': data['data']['list'][i]['post']['subject']
                })
            log.info('获取成功！')
        else:
            log.error(f'获取失败, 原因：{data}')
            raise RuntimeError
        time.sleep(2)
        return articles

    def readArticle(self):
        """浏览3个【大别野】帖子"""
        log.info('正在看帖...')
        for i in range(3):
            resp = requests.get(url=api.detailUrl.format(self.articleList[i]['post_id']),
                             cookies=self.user, headers=self.headers)
            data = resp.json()
            if data['retcode'] == 0:
                log.info(f'看帖 {self.articleList[i]["subject"]} 成功！')
            else:
                log.error(f'看帖 {self.articleList[i]["subject"]} 失败，原因：{data}')
                raise RuntimeError
            time.sleep(2)

    def upVote(self):
        """给5个【大别野】帖子点赞"""
        log.info('正在点赞...')
        for i in range(5):
            resp = requests.post(url=api.voteUrl, cookies=self.user, headers=self.headers,
                              json={'post_id': self.articleList[i]['post_id'], 'is_cancel': False})
            data = resp.json()
            if data['retcode'] == 0:
                log.info(f'点赞 {self.articleList[i]["subject"]} 成功！')
            else:
                log.error(f'点赞 {self.articleList[i]["subject"]} 失败，原因：{data}')
                raise RuntimeError
            time.sleep(2)

    def share(self):
        """分享1个【大别野】帖子"""
        log.info('正在分享...')
        resp = requests.get(url=api.shareUrl.format(self.articleList[0]['post_id']),
                         cookies=self.user, headers=self.headers)
        data = resp.json()
        if data['retcode'] == 0:
            log.info(f'分享 {self.articleList[0]["subject"]} 成功！')
        else:
            log.error(f'分享 {self.articleList[0]["subject"]} 失败，原因：{data}')
            raise RuntimeError
        time.sleep(2)

    def signIn(self):
        """【大别野】打卡"""
        log.info('正在打卡...')
        self.headers['DS'] = api.get_DS2(json.dumps({'gids': self.da_bie_ye['id']}), '')
        resp = requests.post(url=api.signUrl, json={'gids': self.da_bie_ye['id']},
                          cookies=self.user, headers=self.headers)
        data = resp.json()
        if data['retcode'] == 0:
            log.info(f'【大别野】打卡成功！')
        elif data['retcode'] == 1034:
            log.error(f'【大别野】打卡失败，原因：遇到验证码，请使用米游社APP手动打卡')
        else:
            log.error(f'【大别野】打卡失败，原因：{data}')
            raise RuntimeError


def do_myb_task():
    user_list = load_user()
    tools.print_blank_line_and_delay()
    log.info('开始执行米游币任务...')
    for i in range(len(user_list)):
        tools.print_blank_line_and_delay()
        log.warning(f'==开始第{i+1}个账号的米游币任务==')
        myb_task = MiYouBiTask(user_list[i])
        myb_task.readArticle()
        myb_task.upVote()
        myb_task.share()
        myb_task.signIn()


if __name__ == '__main__':
    try:
        do_myb_task()
        tools.print_blank_line_and_delay()
        input('米游币任务已全部执行完毕，请核对以上日志信息，确认无误按回车键退出：')
    except RuntimeError:
        tools.print_blank_line_and_delay()
        input('程序遇到错误，请阅读上方红色红字提示后按回车键终止程序：')
