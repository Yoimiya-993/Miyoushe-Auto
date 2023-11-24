import json
from json.decoder import JSONDecodeError

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from common import stokenUrl, get_Nickname, print_blank_line
from log_config import log


def get_permit_cookie() -> dict:
    """获取米哈游通行证的cookie"""
    log.info('正在启动Edge浏览器...')
    wd = webdriver.Edge(service=Service(r'./msedgedriver.exe'))
    wd.get('https://user.mihoyo.com/')
    log.info('浏览器启动成功，请登录米哈游通行证...')
    # 检测网页上是否还有“登录”按钮
    wait = WebDriverWait(wd, 1)
    while True:
        try:
            wait.until(expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'login-btn')))
        except:
            break
    web_cookie = wd.get_cookies()
    wd.quit()
    permit_cookie = {}
    for ck in web_cookie:
        k, v = ck['name'], ck['value']
        permit_cookie[k] = v
    log.info('获取米哈游通行证cookie成功！')
    return permit_cookie


def get_user_info(permit_cookie) -> dict:
    """通过米哈游通行证cookie获取用户信息"""
    log.info('获取用户信息中...')
    user_info = {'stuid': permit_cookie['account_id']}
    res = requests.get(url=stokenUrl.format(permit_cookie['login_ticket'], user_info['stuid']))
    data = json.loads(res.text.encode('utf-8'))
    if data['retcode'] == 0:
        user_info['stoken'] = data['data']['list'][0]['token']
        log.info('用户信息获取成功！')
    else:
        log.error(f'用户信息获取失败，原因：{data["message"]}')
        raise RuntimeError
    return user_info


def save_user_info(info) -> list[dict]:
    """把用户信息存入json文件

    可能出现的情况：
        1 没有“user_info”文件：
            创建文件->添加用户->保存文件->结束
        2 有“user_info”文件：
            2.1 内容被改动，无法解析json：
                打印错误日志->抛出异常->结束
            2.2 内容没被改动，可以解析json：
                检查这个用户之前是否添加过：
                    2.2.1 没添加过：
                        添加用户->保存文件->结束
                    2.2.2 有添加过（说明原stoken失效，用户在重新登录以更新stoken）：
                        更新用户->保存文件->结束
    """
    nickname = get_Nickname(info['stuid'])
    log.info(f'正在将【{nickname}】的用户信息保存到“user_info”文件...')
    data = []
    try:
        with open('./user_info.json', 'r') as f:
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
        for i in range(len(data)):
            if data[i]['stuid'] == info['stuid']:
                log.info(f'发现用户[{nickname}]已存在，正在更新该用户信息...')
                data[i]['stoken'] = info['stoken']
                cookie_repeated = True
                log.info('用户信息更新成功！')
                break
    if not cookie_repeated:
        data.append(info)
    with open('./user_info.json', 'w') as f:
        json.dump(data, f)
    log.info('保存成功！')
    return data


def main() -> list[dict]:
    permit_cookie = get_permit_cookie()
    print_blank_line()
    user_ck = get_user_info(permit_cookie)
    print_blank_line()
    return save_user_info(user_ck)


if __name__ == '__main__':
    try:
        main()
        print_blank_line()
        input('程序正常结束，按回车键退出：')
    except RuntimeError:
        print_blank_line()
        input('程序遇到错误，请阅读上方红色红字提示后按回车键终止程序：')
