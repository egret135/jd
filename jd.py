#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/3/22 下午5:24
# @Author  : 白鹭
# @email   : zhanghang@linghit.com
# 滑块破解参考：https://github.com/RysisLiang/Trial_Jigsaw
import argparse
import json
import os
import re
import time
import traceback
from base64 import b64decode
import cv2
import nil
import random
import numpy as np
import requests
from selenium import webdriver
from selenium.webdriver import ActionChains


def random_str(length=10):
    init_str = '1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'
    res_str = ''
    for i in range(10):
        r = random.randint(0, len(init_str) - 1)
        res_str += init_str[r]
    return str(res_str)


class JDOrder:
    DEFAULT_MOVE_DURATION = 250

    # 浏览器存放位置
    _binary_location = ''
    # 不打开浏览器运行程序
    _headless = False

    _username = ''
    _password = ''
    _sec_account_no = ''
    _callback_url = ''

    _driver = nil
    _login_url = 'https://passport.shop.jd.com/login/index.action'
    _settlement_url = 'https://fin.shop.jd.com/taurus/billManageIndex#/daybill'
    _query_bill_url = 'https://fin.shop.jd.com/taurus/queryDaybillByPage'
    _query_vender_url = 'https://fin.shop.jd.com/taurus/queryVenderPayList'

    def __init__(self, username, password, binary_location, headless, callback_url):
        self._username = username
        self._password = password
        self._binary_location = binary_location
        self._headless = headless
        self._callback_url = callback_url
        self._init_driver()

    def _init_driver(self):
        chrome_options = webdriver.ChromeOptions()
        if self._binary_location != '':
            chrome_options.binary_location = self._binary_location
        if self._headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 SocketLog(tabid=1007&client_id=1)')
        self._driver = webdriver.Chrome(options=chrome_options)
        self._driver.set_window_rect(0, 0, 1792, 1120)
        self._driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                          get: () => undefined
                        })
                    """
        })

    def close_driver(self):
        self._driver.close()

    def _save_base64(self, image_base64):
        image_base64 = image_base64.split(",")[-1]  # 删除前面的 “data:image/jpeg;base64,”
        image_base64 = image_base64.replace("%0A", '\n')  # 将"%0A"替换为换行符
        image_data = b64decode(image_base64)  # b64decode 解码
        image_path = '/tmp/%s.png' % random_str()
        with open(image_path, 'wb') as fout:
            fout.write(image_data)
            fout.close()
        return image_path

    def _getRadomPauseScondes(self):
        """
        :return:随机的拖动暂停时间
        """
        return random.uniform(0.6, 0.9)

    def _get_tracks(self, distance):
        """
        根据偏移量获取移动轨迹3
        :param distance: 偏移量
        :return: 移动轨迹
        """
        track = []
        mid1 = round(distance * random.uniform(0.1, 0.2))
        mid2 = round(distance * random.uniform(0.65, 0.76))
        mid3 = round(distance * random.uniform(0.84, 0.88))
        # 设置初始位置、初始速度、时间间隔
        current, v, t = 0, 0, 0.2
        distance = round(distance)

        while current < distance:
            # 四段加速度
            if current < mid1:
                a = random.randint(10, 15)
            elif current < mid2:
                a = random.randint(30, 40)
            elif current < mid3:
                a = -70
            else:
                a = random.randint(-25, -18)

            # 初速度 v0
            v0 = v
            # 当前速度 v = v0 + at
            v = v0 + a * t
            v = v if v >= 0 else 0
            move = v0 * t + 1 / 2 * a * (t ** 2)
            move = round(move if move >= 0 else 1)
            # 当前位移
            current += move
            # 加入轨迹
            track.append(move)

        # print("current={}, distance={}".format(current, distance))

        # 超出范围
        back_tracks = []
        out_range = distance - current
        if out_range < -8:
            sub = int(out_range + 8)
            back_tracks = [-1, sub, -3, -1, -1, -1, -1]
        elif out_range < -2:
            sub = int(out_range + 3)
            back_tracks = [-1, -1, sub]

        # print("forward_tracks={}, back_tracks={}".format(track, back_tracks))
        return {'forward_tracks': track, 'back_tracks': back_tracks}

    def _slider_action(self, tracks):
        """
        移动滑块
        :return:
        """
        print("开始移动滑块")

        slider = self._driver.find_element_by_class_name('JDJRV-slide-btn')

        ActionChains(self._driver).click_and_hold(slider).perform()

        # 正向滑动
        for track in tracks['forward_tracks']:
            yoffset_random = random.uniform(-2, 4)
            ActionChains(self._driver).move_by_offset(xoffset=track, yoffset=yoffset_random).perform()

        time.sleep(random.uniform(0.06, 0.5))

        # 反向滑动
        for back_tracks in tracks['back_tracks']:
            yoffset_random = random.uniform(-2, 2)
            ActionChains(self._driver).move_by_offset(xoffset=back_tracks, yoffset=yoffset_random).perform()

        # 抖动
        ActionChains(self._driver).move_by_offset(
            xoffset=self.get_random_float(0, -1.67),
            yoffset=self.get_random_float(-1, 1)
        ).perform()
        ActionChains(self._driver).move_by_offset(
            xoffset=self.get_random_float(0, 1.67),
            yoffset=self.get_random_float(-1, 1)
        ).perform()

        time.sleep(self.get_random_float(0.2, 0.6))
        ActionChains(self._driver).release().perform()

        print("滑块移动成功")
        time.sleep(2)
        return True

    def get_random_float(self, min, max, digits=4):
        """
        :param min:
        :param max:
        :param digits:
        :return:
        """
        return round(random.uniform(min, max), digits)

    def __handle_slider_img(self, image):
        """
        对滑块进行二值化处理
        :param image: cv类型的图片对象
        :return:
        """
        kernel = np.ones((8, 8), np.uint8)  # 去滑块的前景噪声内核
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 灰度化

        # 灰化背景
        width, heigth = gray.shape
        for h in range(heigth):
            for w in range(width):
                if gray[w, h] == 0:
                    gray[w, h] = 96

        # 排除背景
        binary = cv2.inRange(gray, 96, 96)
        res = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)  # 开运算去除白色噪点
        return res

    def _match_template(self, img_target, img_template):
        """
        模板匹配（用于寻找缺口）
        :param img_target: 带有缺口的背景图
        :param img_template: 缺口的滑块图
        :return: 缺口所在的位置的x轴距离
        """
        print("图片缺口模板匹配")

        img_target = cv2.imread(img_target)
        img_template = cv2.imread(img_template)

        # 滑块图片处理
        tpl = self.__handle_slider_img(img_template)  # 误差来源就在于滑块的背景图为白色

        # 图片高斯滤波
        blurred = cv2.GaussianBlur(img_target, (3, 3), 0)

        # 图片灰度化
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

        width, height = tpl.shape[:2]

        # 灰度化模板匹配
        result = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)  # 使用灰度化图片
        # print("result = {}".format(len(np.where(result >= 0.5)[0])))

        # 查找数组中匹配的最大值
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        left_up = max_loc
        right_down = (left_up[0] + height, left_up[1] + width)
        cv2.rectangle(img_target, left_up, right_down, (7, 279, 151), 2)
        print('匹配结果区域起点x坐标为：%d' % max_loc[0])

        return left_up[0]

    def _check_slider(self):
        # 检测是否需要滑块验证
        while True:
            print('进行滑块验证')

            current_url = self._driver.current_url

            if not re.search('login', current_url):
                break

            bg_base64 = self._driver.find_element_by_xpath('//div[@class="JDJRV-bigimg"]/img').get_attribute('src')

            slider_base64 = self._driver.find_element_by_xpath('//div[@class="JDJRV-smallimg"]/img').get_attribute(
                'src')

            bg_path = self._save_base64(bg_base64)

            slider_path = self._save_base64(slider_base64)

            distance = self._match_template(bg_path, slider_path)

            distance = distance * 281 / 360

            print('滑块偏移长度：{}'.format(distance))

            # 获取滑块移动轨迹
            tracks = self._get_tracks(distance)

            # 滑动滑块
            self._slider_action(tracks=tracks)

            os.unlink(bg_path)

            os.unlink(slider_path)

    def _check_phone(self):
        # 检测是否需要手机号验证
        current_url = self._driver.current_url

        # 短信验证码
        if re.search('securityProtect', current_url):
            self._driver.find_element_by_link_text('短信验证').click()
            time.sleep(1.5)
            self._driver.find_element_by_link_text('发送验证码').click()
            while True:
                print('需要输入手机号验证码登录，请在手机上查看：')
                code = input()
                self._driver.find_element_by_id('pcode').send_keys(code)
                time.sleep(2)
                self._driver.find_element_by_id('checkCode').click()
                time.sleep(2)
                current_url = self._driver.current_url
                if re.search('securityProtect', current_url):
                    print('验证码错误，请重新输入')
                    continue
                break

    def _get_mert_info(self):
        res = requests.post(self._query_vender_url, headers=self.get_header(), data=json.dumps({}), timeout=10)
        result = res.content
        print('获取商户信息响应码：{0}，响应内容：{1}'.format(res.status_code, result))
        if res.status_code != 200:
            raise BaseException('获取商户信息失败')
        result = json.loads(result)

        self._sec_account_no = result['data'][0]['secAccountNo']

    def login(self):
        """
        登录
        :return: nil
        """
        self._driver.get(self._login_url)
        time.sleep(2)

        self._driver.find_element_by_id('account-login').click()
        time.sleep(1)

        self._driver.switch_to.frame('loginFrame')

        login_name = self._driver.find_element_by_id('loginname')
        login_name.send_keys(self._username)

        time.sleep(1.5)

        login_pwd = self._driver.find_element_by_id('nloginpwd')
        login_pwd.send_keys(self._password)

        time.sleep(1.5)

        self._driver.find_element_by_id('paipaiLoginSubmit').click()

        time.sleep(0.5)

        # 检测是否需要滑块验证
        self._check_slider()

        # 检测是否需要手机号验证
        self._check_phone()

        print('登录成功')

        # 跳转至结算页面
        self._driver.get(self._settlement_url)

        # 获取商户信息
        self._get_mert_info()

    def query_order(self, begin_date, end_date, status=2, date_type=2, begin_end_date=None, total=0):
        # 爬取账单数据
        begin_date = time.strptime(begin_date, "%Y-%m-%d")
        end_date = time.strptime(end_date, "%Y-%m-%d")
        begin_date = int(time.mktime(begin_date)) * 1000
        end_date = (int(time.mktime(end_date)) + 86400 - 1) * 1000 + 999

        page = 1
        while True:
            data = {
                'beginEndDate': begin_end_date,
                'dateType': int(date_type),
                'pageNum': page,
                'pageSize': 20,
                'secAccountNo': self._sec_account_no,
                'setDateBegin': begin_date,
                'setDateEnd': end_date,
                'status': int(status),
                'total': int(total)
            }
            print(data)
            res = requests.post(self._query_bill_url, headers=self.get_header(), data=json.dumps(data), timeout=10)
            result = res.content
            print('获取账单接口响应码：{0}，响应内容：{1}'.format(res.status_code, result))
            if res.status_code != 200:
                raise BaseException('获取账单接口请求失败')
            else:
                print('获取账单接口请求成功，页数：{0}'.format(page))
                if self._callback_url != '':
                    local_headers = {
                        'Content-Type': 'application/json'
                    }
                    try:
                        res = requests.post(self._callback_url, headers=local_headers, data=str(result), timeout=10)
                        print('请求回调地址响应码：{0}，响应内容：{1}'.format(res.status_code, res.content))
                    except Exception:
                        print('请求回调地址出现异常：{0}'.format(traceback.print_exc()))
                result = json.loads(result)
                if result['totalCount'] > (result['pageNum'] * result['pageSize']):
                    page += 1
                    total = result['totalCount']
                    continue
                break

    def get_cookie(self):
        cookie = ''
        for elem in self._driver.get_cookies():
            cookie += elem["name"] + "=" + elem["value"] + "; "
        cookie = cookie[:-2]
        return cookie

    def get_header(self):
        headers = {
            'referer': 'https://fin.shop.jd.com/taurus/billManageIndex',
            'content-type': 'application/json;charset=UTF-8',
            'accept': 'application/json, text/plain, */*',
            'origin': 'https://fin.shop.jd.com',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 SocketLog(tabid=419&client_id=1)',
            'cookie': self.get_cookie()
        }
        return headers


username = ''
password = ''
start_time = ''
end_time = ''
status = None
binary_location = ''
headless = False
callback_url = ''
begin_end_date = None
date_type = None

DATE_TYPE = {
    '1': '收款到账日期',
    '2': '账单日期'
}

STATUS = {
    '0': '代收款',
    '1': '收款中',
    '2': '已收款'
}

if __name__ == '__main__':
    parse = argparse.ArgumentParser()
    parse.add_argument('-s', '--start', help='抓取订单起始日期，格式为：Y-m-d', required=True, dest='start_time')
    parse.add_argument('-e', '--end', help='抓取订单结束日期，格式为：Y-m-d', required=True, dest='end_time')
    parse.add_argument('-u', '--username', help='京东商家账号', required=True, dest='username')
    parse.add_argument('-p', '--password', help='京东商家密码', required=True, dest='password')
    parse.add_argument('-n', '--begin-end-date', default=None, help='begin_end_date', dest='begin_end_date')
    parse.add_argument('-a', '--date-type', default='2', choices=['1', '2'], help='日期类型：1-收款到账日期，2-账单日期',
                       dest='date_type')
    parse.add_argument('-t', '--status', default='2', choices=['0', '1', '2'],
                       help='收款状态，0-代收款，1-收款中，2-已收款', dest='status')
    parse.add_argument('-b', '--binary-location', default='', help='浏览器可执行文件路径', dest='binary_location')
    parse.add_argument('-d', '--headless', action='store_true', help='不开启浏览器执行程序', dest='headless')
    parse.add_argument('-c', '--callback-url', default='', help='结果数据回调链接', dest='callback_url')
    args = parse.parse_args()
    pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    if not pattern.match(args.start_time) or not pattern.match(args.end_time):
        print('日期格式必须为Y-m-d')
        exit(1)
    print("抓取订单起始日期：{0}".format(args.start_time))
    print("抓取订单结束日期：{0}".format(args.end_time))
    print("begin_end_date：{0}".format(args.begin_end_date))
    print("日期类型：{0}".format(DATE_TYPE[args.date_type]))
    print("收款状态：{0}".format(STATUS[args.status]))
    print("订单数据回调链接：{0}".format(args.callback_url))
    if args.headless:
        print("不打开浏览器")
    start_time = args.start_time
    end_time = args.end_time
    username = args.username
    password = args.password
    date_type = args.date_type
    begin_end_date = args.begin_end_date
    status = args.status
    binary_location = args.binary_location
    headless = args.headless
    callback_url = args.callback_url

try:
    jd = JDOrder(username=username, password=password, binary_location=binary_location, headless=headless,
                 callback_url=callback_url)
    jd.login()
    jd.query_order(begin_date=start_time, end_date=end_time, status=status, date_type=date_type,
                   begin_end_date=begin_end_date)
    jd.close_driver()
    print('订单抓取完成')
except Exception:
    print('请求出现异常：{0}'.format(traceback.print_exc()))
    jd.close_driver()
