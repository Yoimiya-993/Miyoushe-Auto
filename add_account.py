import os
import json
import time
import multiprocessing as mp
import tkinter as tk
import tools
import api
import constant
from PIL import ImageTk
from json.decoder import JSONDecodeError
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.common.exceptions import NoSuchDriverException, SessionNotCreatedException
from log_config import log
from request import http


# def get_permit_cookie() -> dict:
#     """获取米哈游通行证的cookie"""
#     log.info('正在启动Edge浏览器...')
#     edge_options = webdriver.EdgeOptions()
#     edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])
#     wd = webdriver.Edge(service=Service(r'./msedgedriver.exe'), options=edge_options)
#     wd.get('https://user.mihoyo.com/#/login/captcha')
#     log.info('浏览器启动成功，请登录米哈游通行证...')
#     # 检测用户是否登录了
#     while True:
#         time.sleep(1)
#         if wd.current_url == 'https://user.mihoyo.com/#/account/home':
#             break
#     web_cookie = wd.get_cookies()
#     wd.quit()
#     permit_cookie = {ck['name']: ck['value'] for ck in web_cookie}
#     log.info('获取米哈游通行证login_ticket成功！')
#     return permit_cookie


def get_user_info(permit_cookie) -> dict:
    """通过米哈游通行证cookie获取用户信息"""
    log.info('正在通过login_ticket获取stoken...')
    user_info = {'uid': permit_cookie['login_uid']}
    resp = http.get(url=api.stokenUrl.format(permit_cookie['login_ticket'], user_info['uid']))
    data = resp.json()
    if data['retcode'] == 0:
        user_info['stoken'] = data['data']['list'][0]['token']
        log.info('获取stoken成功！')
    else:
        log.error(f'获取stoken失败，原因：{data["message"]}')
        raise RuntimeError
    return user_info


def save_user_info(info) -> list[dict[str, str]]:
    """把用户信息存入json文件"""
    nickname = api.get_bbs_nickname(info['uid'])
    log.info(f'正在将【{nickname}】的用户信息保存到“user_info”文件...')
    data = []
    try:
        with open('./data/user_info.json', 'r') as f:
            log.info('检测到“user_info”文件已存在，正在读取文件原内容...')
            data = json.load(f)
    except FileNotFoundError:
        pass
    except JSONDecodeError:
        log.error('文件“user_info”原内容读取失败，请不要改动文件内容！如有改动，请删除原文件再重新登录之前存储过的用户')
        raise RuntimeError
    cookie_repeated = False
    if len(data):
        log.info('文件“user_info”原内容读取完毕！')
        log.info(f'正在添加【{nickname}】的用户信息...')
        for i in range(len(data)):
            if data[i]['uid'] == info['uid']:
                log.info(f'发现用户[{nickname}]已存在，正在更新该用户信息...')
                data[i]['stoken'] = info['stoken']
                if 'mid' in info:
                    data[i]['mid'] = info['mid']
                cookie_repeated = True
                log.info('用户信息更新成功！')
                break

    if not cookie_repeated:
        data.append(info)
    if not os.path.exists('./data'):
        os.mkdir('./data')
    with open('./data/user_info.json', 'w') as f:
        json.dump(data, f, indent=4)
    log.info('保存成功！')
    return data


def add_account_by_browser() -> list[dict[str, str]]:
    try:
        permit_cookie = get_permit_cookie()
        user_ck = get_user_info(permit_cookie)
        return save_user_info(user_ck)
    except NoSuchDriverException:
        log.error('缺失msedgedriver.exe文件')
        raise RuntimeError
    except SessionNotCreatedException:
        log.error('msedgedriver.exe的版本与浏览器不兼容')
        raise RuntimeError


def add_account_by_scan_qrcode():
    """通过扫码登录添加账号"""
    log.info('正在生成二维码...')
    app_id = constant.GENSHIN_APPID
    url, ticket = api.fetch_qrcode(app_id)
    if url is None:
        log.error(f'生成二维码失败，原因：{ticket}')
        raise RuntimeError
    # 创建子进程显示二维码图片
    qrcode_display_process = mp.Process(target=display_qrcode, args=(url, qrcode_manual_close), daemon=True)
    qrcode_display_process.start()
    log.info('打开米游社扫描出现的二维码')
    # 不断查询二维码状态
    while True:
        time.sleep(1)
        qrcode_status, data = api.query_qrcode_status(app_id, ticket)
        # 当二维码 已过期/已确认/手动被关闭 时，退出查询
        if qrcode_status == constant.QRCODE_EXPIRED or qrcode_status == constant.QRCODE_CONFIRMED \
                or qrcode_manual_close.value:
            break
    # 程序走到这里说明该二维码已完成他的使命，应该关闭子进程
    qrcode_display_process.terminate()
    qrcode_display_process.join()
    if qrcode_manual_close.value:
        qrcode_manual_close.value = False
        return log.warning('你关闭了二维码窗口')
    elif qrcode_status == constant.QRCODE_EXPIRED:
        return log.warning('二维码已过期')
    log.info('扫码成功，正在通过game_token获取stoken和mid...')
    stoken, mid = api.get_stoken_by_game_token(int(data['uid']), data['token'])
    account = {'uid': data['uid'], 'stoken': stoken, 'mid': mid}
    if account['stoken'] is None:
        raise RuntimeError
    return save_user_info(account)


# 二维码被手动关闭（进程信号量，用于判断是否要关闭进程）
qrcode_manual_close = mp.Value('b', False)


class QrcodeWindow(tk.Tk):
    def __init__(self, data, manual_close):
        super().__init__()
        qrcode = tools.generate_qrcode_image(data)
        self.manual_close = manual_close
        tk_image = ImageTk.PhotoImage(image=qrcode)
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        window_width, window_height = tk_image.width(), tk_image.height()
        x, y = (screen_width - window_width) // 2, (screen_height - window_height) // 2
        self.geometry('+{}+{}'.format(x, y))
        label = tk.Label(self, image=tk_image)
        label.image = tk_image
        label.pack(padx=0, pady=0)
        self.resizable(False, False)
        self.attributes('-topmost', True)
        self.protocol('WM_DELETE_WINDOW', self.on_closing)

    def on_closing(self):
        self.manual_close.value = True
        self.destroy()


def display_qrcode(data, manual_close):
    """显示二维码"""
    qrcode_window = QrcodeWindow(data, manual_close)
    qrcode_window.mainloop()


if __name__ == '__main__':
    try:
        # add_account_by_browser()
        while True:
            add_account_by_scan_qrcode()
            tools.print_blank_line_and_delay()
            input('回车继续添加账号，要退出直接关闭程序')
    except RuntimeError:
        tools.print_blank_line_and_delay()
        input('程序遇到错误，请阅读上方红色红字提示后按回车键终止程序：')
