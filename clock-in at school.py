# encoding:utf-8
import base64
import json
import requests
import sys
import time

from requests import utils
import util

info = {
    'id': '201726010509',
    'pwd': 'Creddit2020!',
    'location': '湖南省/长沙市/岳麓区',
    'detail': '湖大',
    'temperature': '36.0'  # 离校时不需要
}


def get_token():
    try:
        response = requests.get('https://fangkong.hnu.edu.cn/api/v1/account/getimgvcode')

    except requests.exceptions.RequestException:
        raise Exception('获取登录token超时，网络环境异常')

    else:
        res_json = response.json()
        if res_json['code'] == 0 and res_json['msg'] == '成功':
            return res_json['data']['Token']

        else:
            raise Exception('获取登录token失败 ' + res_json['msg'])


def get_img_code():
    token = get_token()

    img_url = 'https://fangkong.hnu.edu.cn/imagevcode?token={0}'.format(token)

    try:
        response = requests.get(img_url)

    except requests.exceptions.RequestException as e:
        raise Exception('获取验证码图片超时，网络环境异常')
    else:
        url_content = response.content
        img_base64 = base64.b64encode(url_content)

        try:
            var_code = util.baidu_ocr(img_base64)
            return token, var_code

        except Exception as e:
            # 这个怕访问次数太多了扣钱，所以错误了就停了~
            print(e)
            sys.exit(-1)


def sign_in():
    token, var_code = get_img_code()

    sign_in_dict = {
        'Code': info['id'],
        'Password': info['pwd'],
        'Token': token,
        'VerCode': var_code,
        'WechatUserinfoCode': ''
    }

    sign_in_headers = {
        'Content-Type': 'application/json;charset=UTF-8',

        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/88.0.4324.96 Safari/537.36 '
                      'Edg/88.0.705.56'
    }

    try:
        response = requests.post('https://fangkong.hnu.edu.cn/api/v1/account/login',
                                 headers=sign_in_headers,
                                 data=json.dumps(sign_in_dict))

    except requests.exceptions.RequestException:
        raise Exception('连接超时，网络环境异常')

    else:
        res_json = response.json()
        if res_json['code'] == 0 and res_json['msg'] == '成功':
            cookies = requests.utils.dict_from_cookiejar(response.cookies)

            timestamp = str(int(time.time()))

            clock_in_headers = {
                'Accept': 'application/json, text/plain, */*',

                'Accept-Encoding': 'gzip, deflate, br',

                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',

                'Connection': 'keep-alive',

                'Host': 'fangkong.hnu.edu.cn',

                'Content-Type': 'application/json;charset=UTF-8',

                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/88.0.4324.96 Safari/537.36 '
                              'Edg/88.0.705.56',

                'Sec-Fetch-Site': 'same-origin',

                'Sec-Fetch-Mode': 'cors',

                'Sec-Fetch-Dest': 'empty',

                'Origin': 'https://fangkong.hnu.edu.cn',

                'Referer': 'https://fangkong.hnu.edu.cn/app/',

                'Cookie': "Hm_lvt_d7e34467518a35dd690511f2596a570e=" + timestamp + ";"
                          "TOKEN=" + cookies["TOKEN"] + ";"
                          ".ASPXAUTH=" + cookies[".ASPXAUTH"]
            }

            print(util.get_local_time(), '登录成功')


            return clock_in_headers

        else:
            raise Exception('登录失败 ' + res_json['msg'])


def clock_in(type, clock_in_headers):
    # type 打卡模式

    clock_in_dict = util.default_request_payload

    locations = info['location'].split('/')

    #print(clock_in_dict)

    try:
        response = requests.post('https://fangkong.hnu.edu.cn/api/v1/clockinlog/add',
                                 headers=clock_in_headers,
                                 data=json.dumps(clock_in_dict))

    except requests.exceptions.RequestException:
        raise Exception('连接超时，网络环境异常')

    else:
        res_json = response.json()
        if res_json['code'] == 0 and res_json['msg'] == '成功':

            print(util.get_local_time(), '签到成功')

            return True

        else:
            raise Exception('签到失败 ' + res_json['msg'])


def main():
    while True:
        try:
            headers = sign_in()

        except Exception as e:
            print(util.get_local_time(), e)
            print('五秒后重试...')
            time.sleep(5)

        else:
            try:
                clock_in('atschool', headers)

            except Exception as e:
                print(util.get_local_time(), e)
                print('五秒后重试...')
                time.sleep(5)

            else:
                break


if __name__ == '__main__':
    main()