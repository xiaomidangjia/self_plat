import importlib
import sys
import os
import urllib
import requests
import base64
import json
from datetime import datetime
import time
import pandas as pd
import numpy as np
import random
import hmac
# =========在此设置api-key，下单金额===========
# 默认设置BTC订单，不要修改
crypto = 'btc'
crypto_usdt = 'BTC_USDT'
base_num = 0.01
crypto_name = 'BTC'
# 设置api-key，注意试用期只有3个月有效期
api_key = 'E75LQUK39S62'
API_URL = 'https://api.bitget.com'
API_SECRET_KEY = "c3dcf7ed5f80ec7b30a3af7e4dc847efe95be64d66570e667af82fc43192a250"
API_KEY = "bg_e6fd3c23efbe7aa2a09dc8862275a812"
PASSPHRASE = "MMClianghua666"
# 设置每一单BTC的U本位合约时的购买U数
order_value = 30
# 设置永续合约的开单倍数，倍数不超过25倍
multiple = 25
# ================================================================================================================================================
def get_timestamp():
    return int(time.time() * 1000)
def sign(message, secret_key):
    mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    d = mac.digest()
    return base64.b64encode(d)
def pre_hash(timestamp, method, request_path, body):
    return str(timestamp) + str.upper(method) + request_path + body
def parse_params_to_str(params):
    url = '?'
    for key, value in params.items():
        url = url + str(key) + '=' + str(value) + '&'
    return url[0:-1]
def get_header(api_key, sign, timestamp, passphrase):
    header = dict()
    header['Content-Type'] = 'application/json'
    header['ACCESS-KEY'] = api_key
    header['ACCESS-SIGN'] = sign
    header['ACCESS-TIMESTAMP'] = str(timestamp)
    header['ACCESS-PASSPHRASE'] = passphrase
    # header[LOCALE] = 'zh-CN'
    return header
# ================================================================================================================================================
finish_date = []
total_income = []
# 第二个log日志打印接口,每隔60s打印一次
w2 = 0 
p2 = 0
#每天定时监控下单
while True:
    #获取当前日期
    date = str(datetime.utcnow())[0:10]
    week_day = pd.to_datetime(date).weekday()
    #获取u本位合约账户usdt
    # GET 合约账户
    timestamp = get_timestamp()
    response = None
    request_path_mix = "/api/mix/v1/account/account"
    params_mix = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT"}
    request_path_mix = request_path_mix + parse_params_to_str(params_mix)
    url = API_URL + request_path_mix
    body = ""
    sign_mix = sign(pre_hash(timestamp, "GET", request_path_mix,str(body)), API_SECRET_KEY)
    header_mix = get_header(API_KEY, sign_mix, timestamp, PASSPHRASE)
    response_mix = requests.get(url, headers=header_mix)
    response_1 = json.loads(response_mix.text)
    mix_value = float(response_1['data']['available'])
    print("合约账户USDT余额 : ",mix_value)
    #判断是不是要把现货u转入usdt
    if mix_value < order_value*1.03:
        #从现货转入
        timestamp = get_timestamp()
        response = None
        tranfer_value = int(order_value*1.03 - mix_value) + 10
        request_path = "/api/spot/v1/wallet/transfer-v2"
        url = API_URL + request_path
        params = {"fromType":"spot","toType":"mix_usdt","amount": str(tranfer_value),"coin": "USDT"}
        body = json.dumps(params)
        sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
        header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
        response_spot = requests.post(url, data=body, headers=header)
        response_spot_1 = json.loads(response_spot.text)
        response_spot_res = response_spot_1['data']['transferId']
        print("现货向合约划转的ID : ",str(response_spot_res))
    else:
        print('不需要划转')

    if date in finish_date:
        if p2 % 3600 ==0:
            print('今天已经完成订单，不需要继续下单')
        time.sleep(1)
        p2 += 1
        continue
    else:
        # 第一个log日志打印接口,每隔60s打印一次
        w1 = 0
        flag = 0
        while flag == 0:
            time.sleep(1)
            #调用接口  
            try:
                test_data_1 = {
                    "date": date,
                    "api_key":api_key,
                    "order_value":order_value
                    }
                req_url = "http://8.219.100.91:5080/third_crypto_pre"
                r = requests.post(req_url, data=test_data_1)
                api_res = r.content.decode('utf-8')
                api_res = json.loads(api_res)
                api_value = api_res['value']
                api_pingjia = api_res['pingjia']
                api_risk = float(api_res['risk'])
            except:
                continue
            if api_value == 'error':
                if w1%30==0:
                    print('数据没有跑完')
                w1 += 1
            elif api_value == 'no_api':
                while True:
                    print('无效api—key，或者无效的ip地址，请购买正版，或不要与他人共享api-key')
                    time.sleep(1)
            elif api_value == 'exit_date':
                while True:
                    print('已经超过api-key使用时间，请购买正版或续费')
                    time.sleep(1)
            elif api_value == 'exit_value':
                while True:
                    print('已经超出试用api-key能下单的最大金额，试用api-key最大U本位合约为200U,正式版最大为20000u')
                    time.sleep(1)
            else:
                flag = 1
        # 价格达不到，或者时间达不到不开单
        if api_pingjia == 'unknow_reason':
            if w2 % 3600 == 0:
                print('数据已经跑完，判断为不下单')
            w2 += 1
            continue
        else:
            if api_pingjia in ('duotou_finish_kill','kongtou_ing_kill','kongtou_start_kill','duotou_main','kongtou_continue_kill'):
                order_type = 1 # 开多
            elif api_risk > 0.25:
                order_type = 2 # 开空
            else:
                order_type = 3   # 开空
            if order_type == 1:
                print('数据已经跑完，下多单')
                # 获得实时交易数据，进行下单判断
                order_list = []
                w5 = 0 
                while w5 == 0:
                    timestamp = get_timestamp()
                    response = None
                    request_path = "/api/mix/v1/market/ticker"
                    url = API_URL + request_path
                    params = {"symbol":"BTCUSDT_UMCBL"}
                    request_path = request_path + parse_params_to_str(params)
                    url = API_URL + request_path
                    body = ""
                    sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                    header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                    response = requests.get(url, headers=header)
                    ticker = json.loads(response.text)
                    eth_price = float(ticker['data']['last'])
                    if eth_price > 0:
                        w5 = 1
                    else:
                        w5 = 0
                second = 0
                s = 0
                price_m = [eth_price]
                while s ==0:
                    time.sleep(1)
                    second += 1
                    if second % 180 == 0:
                        w7 = 0 
                        while w7 == 0:
                            timestamp = get_timestamp()
                            response = None
                            request_path = "/api/mix/v1/market/ticker"
                            url = API_URL + request_path
                            params = {"symbol":"BTCUSDT_UMCBL"}
                            request_path = request_path + parse_params_to_str(params)
                            url = API_URL + request_path
                            body = ""
                            sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                            header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                            response = requests.get(url, headers=header)
                            ticker = json.loads(response.text)
                            eth_price_d = float(ticker['data']['last'])
                            if eth_price_d > 0:
                                w7 = 1 
                            else:
                                w7 = 0 
                        print('正在监控价格',str(eth_price_d) + '前次价格' +str(price_m[0])) 
                        if  eth_price_d -  price_m[0] < 0:
                            s = 0
                            price_m[0] =  eth_price_d
                        else:
                            #合约买入
                            buy_num = round(order_value*multiple/eth_price_d,2)
                            logo_b = 0
                            while logo_b == 0:
                                time.sleep(1)
                                # 调整保证金模式（全仓/逐仓）
                                timestamp = get_timestamp()
                                response = None
                                request_path = "/api/mix/v1/account/setMarginMode"
                                url = API_URL + request_path
                                params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","marginMode": "fixed"}
                                body = json.dumps(params)
                                sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                                header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                                response = requests.post(url, data=body, headers=header)
                                response_1 = json.loads(response.text)
                                response_1_res = response_1['data']['marginMode']
                                print("调整保证金模式 : ",response_1_res)
                                # 下单
                                timestamp = get_timestamp()
                                response = None
                                clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                                request_path = "/api/mix/v1/order/placeOrder"
                                url = API_URL + request_path
                                params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"open_long","size":str(buy_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                                body = json.dumps(params)
                                sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                                header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                                response = requests.post(url, data=body, headers=header)
                                buy_res = json.loads(response.text)
                                buy_id = int(buy_res['data']['orderId'])
                                print("下多单结果 : ",buy_id)
                                if int(buy_id)  > 10:
                                    logo_b = 1
                                else:
                                    logo_b = 0
                            order_list.append(buy_id)
                            #当前合约持仓
                            timestamp = get_timestamp()
                            response = None
                            request_path = "/api/mix/v1/position/singlePosition-v2"
                            url = API_URL + request_path
                            params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT"}
                            request_path = request_path + parse_params_to_str(params)
                            url = API_URL + request_path
                            body = ""
                            sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                            header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                            response = requests.get(url, headers=header)
                            response_3 = json.loads(response.text)
                            response_3_res = response_3['data']
                            for i in range(len(response_3_res)):
                                margin = response_3_res[i]['margin']
                                leverage = response_3_res[i]['leverage']
                                marginMode = response_3_res[i]['marginMode']
                                holdSide = response_3_res[i]['holdSide']
                                if holdSide == 'long':
                                    text = '开多仓结果--------'
                                else:
                                    text = '开空仓结果--------'
                                print(text,"保证金数量 : ",margin,"杠杆倍数: ",leverage,'保证金模式',marginMode,'开仓方向',holdSide)
                            
                            s = 1
                    else:
                        s = 0
            elif order_type in (2,3):
                #开空单，依赖汇率
                print('数据已经跑完，下空单')
                # 获得实时交易数据，进行下单判断
                order_list = []
                w5 = 0 
                while w5 == 0:
                    timestamp = get_timestamp()
                    response = None
                    request_path = "/api/mix/v1/market/ticker"
                    url = API_URL + request_path
                    params = {"symbol":"BTCUSDT_UMCBL"}
                    request_path = request_path + parse_params_to_str(params)
                    url = API_URL + request_path
                    body = ""
                    sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                    header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                    response = requests.get(url, headers=header)
                    ticker = json.loads(response.text)
                    eth_price = float(ticker['data']['last'])
                    if eth_price > 0:
                        w5 = 1
                    else:
                        w5 = 0
                second = 0
                s = 0
                price_m = [eth_price]
                while s ==0:
                    time.sleep(1)
                    second += 1
                    #Log('秒数',second)
                    if second % 180 == 0:
                        w7 = 0 
                        while w7 == 0:
                            timestamp = get_timestamp()
                            response = None
                            request_path = "/api/mix/v1/market/ticker"
                            url = API_URL + request_path
                            params = {"symbol":"BTCUSDT_UMCBL"}
                            request_path = request_path + parse_params_to_str(params)
                            url = API_URL + request_path
                            body = ""
                            sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                            header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                            response = requests.get(url, headers=header)
                            ticker = json.loads(response.text)
                            eth_price_d = float(ticker['data']['last'])
                            if eth_price_d > 0:
                                w7 = 1 
                            else:
                                w7 = 0 
                        print('正在监控价格',str(eth_price_d) + '前次价格' +str(price_m[0])) 
                        if  eth_price_d -  price_m[0] > 0:
                            s = 0
                            price_m[0] =  eth_price_d
                        else:
                            #合约买入
                            sell_num = round(order_value*multiple/eth_price_d,2)
                            logo_b = 0
                            while logo_b == 0:
                                time.sleep(1)
                                # 调整保证金模式（全仓/逐仓）
                                timestamp = get_timestamp()
                                response = None
                                request_path = "/api/mix/v1/account/setMarginMode"
                                url = API_URL + request_path
                                params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","marginMode": "fixed"}
                                body = json.dumps(params)
                                sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                                header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                                response = requests.post(url, data=body, headers=header)
                                response_1 = json.loads(response.text)
                                response_1_res = response_1['data']['marginMode']
                                print("调整保证金模式 : ",response_1_res)
                                # 下单
                                timestamp = get_timestamp()
                                response = None
                                clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                                request_path = "/api/mix/v1/order/placeOrder"
                                url = API_URL + request_path
                                params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"open_short","size":str(sell_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                                body = json.dumps(params)
                                sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                                header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                                response = requests.post(url, data=body, headers=header)
                                sell_res = json.loads(response.text)
                                sell_id = int(sell_res['data']['orderId'])
                                print("下空单结果 : ",sell_id)
                                if int(sell_id)  > 10:
                                    logo_b = 1
                                else:
                                    logo_b = 0
                            order_list.append(sell_id)
                            #当前合约持仓
                            timestamp = get_timestamp()
                            response = None
                            request_path = "/api/mix/v1/position/singlePosition-v2"
                            url = API_URL + request_path
                            params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT"}
                            request_path = request_path + parse_params_to_str(params)
                            url = API_URL + request_path
                            body = ""
                            sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                            header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                            response = requests.get(url, headers=header)
                            response_3 = json.loads(response.text)
                            print(response_3)
                            response_3_res = response_3['data']
                            for i in range(len(response_3_res)):
                                margin = response_3_res[i]['margin']
                                leverage = response_3_res[i]['leverage']
                                marginMode = response_3_res[i]['marginMode']
                                holdSide = response_3_res[i]['holdSide']
                                if holdSide == 'long':
                                    text = '开多仓结果--------'
                                else:
                                    text = '开空仓结果--------'
                                print(text,"保证金数量 : ",margin,"杠杆倍数: ",leverage,'保证金模式',marginMode,'开仓方向',holdSide)
                            s = 1
                    else:
                        s = 0
            else:
                print('发生了未知错误，不能下单')
                time.sleep(1)
                continue                
        time.sleep(1)
        print("order_list", order_list)
        if len(order_list) > 0:
            real_eth_price = eth_price_d
        else:
            continue
        #对订单是否要进行平仓进行判断
        if order_type == 1:
            w3 = 0
            while len(order_list)>0:
                time.sleep(1)
                #目前的eth价格
                w7 = 0 
                while w7 == 0:
                    timestamp = get_timestamp()
                    response = None
                    request_path = "/api/mix/v1/market/ticker"
                    url = API_URL + request_path
                    params = {"symbol":"BTCUSDT_UMCBL"}
                    request_path = request_path + parse_params_to_str(params)
                    url = API_URL + request_path
                    body = ""
                    sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                    header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                    response = requests.get(url, headers=header)
                    now_ticker = json.loads(response.text)
                    now_eth_price = float(now_ticker['data']['last'])
                    if now_eth_price > 0:
                        w7 = 1 
                    else:
                        w7 = 0
                bod = (now_eth_price - real_eth_price)/ real_eth_price
                time_now = str(datetime.utcnow())[0:19]
                time_dd = time_now[0:10]
                time_hh = time_now[11:16]
                if w3 % 600 ==0:
                    print('正在监控价格',str(bod) + '====' +str(real_eth_price))
                if time_hh == '23:59':
                    print('卖出平多仓',now_eth_price)
                    logo_s = 0
                    while logo_s == 0:
                        time.sleep(1)
                        # 平多
                        timestamp = get_timestamp()
                        response = None
                        clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                        request_path = "/api/mix/v1/order/placeOrder"
                        url = API_URL + request_path
                        params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_long","size":str(buy_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                        body = json.dumps(params)
                        sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                        header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                        response = requests.post(url, data=body, headers=header)
                        sell_res = json.dumps(response.text)
                        sell_id = int(sell_res['data']['orderId'])
                        if int(sell_id)  > 10:
                            logo_s = 1
                        else:
                            logo_s = 0
                    del order_list[0]
                    finish_date.append(str(datetime.utcnow())[0:10])
                    print('finish_date',sell_id,finish_date)
                    w2 = 0 
                    p2 = 0                    
                elif bod <= -0.003:
                    print('卖出平多仓监控中')
                    time.sleep(3)
                    w8 = 0 
                    while w8 == 0:
                        timestamp = get_timestamp()
                        response = None
                        request_path = "/api/mix/v1/market/ticker"
                        url = API_URL + request_path
                        params = {"symbol":"BTCUSDT_UMCBL"}
                        request_path = request_path + parse_params_to_str(params)
                        url = API_URL + request_path
                        body = ""
                        sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                        header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                        response = requests.get(url, headers=header)
                        next_ticker = json.loads(response.text)
                        next_eth_price = float(next_ticker['data']['last'])
                        if next_eth_price > 0:
                            w8 = 1 
                        else:
                            w8 = 0
                    next_bod = (next_eth_price - real_eth_price)/ real_eth_price
                    if next_bod <= -0.003:
                        print('卖出平多仓',next_eth_price)
                        logo_s = 0
                        while logo_s == 0:
                            time.sleep(1)
                            # 平多
                            timestamp = get_timestamp()
                            response = None
                            clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                            request_path = "/api/mix/v1/order/placeOrder"
                            url = API_URL + request_path
                            params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_long","size":str(buy_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                            body = json.dumps(params)
                            sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                            header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                            response = requests.post(url, data=body, headers=header)
                            sell_res = json.dumps(response.text)
                            sell_id = int(sell_res['data']['orderId'])
                            if int(sell_id)  > 10:
                                logo_s = 1
                            else:
                                logo_s = 0
                        del order_list[0]
                        finish_date.append(str(datetime.utcnow())[0:10])
                        print('finish_date',sell_id,finish_date)
                        w2 = 0 
                        p2 = 0
                    else:
                        print('回归到正常价格监控中')
                        w3 += 1
                        continue
                elif bod > 0.002:
                    out_order_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
                    out_order_price = str(now_eth_price)
                    time.sleep(60)
                    w4 = 0
                    while len(order_list) > 0:
                        time.sleep(1)
                        w9 = 0 
                        while w9 == 0:
                            timestamp = get_timestamp()
                            response = None
                            request_path = "/api/mix/v1/market/ticker"
                            url = API_URL + request_path
                            params = {"symbol":"BTCUSDT_UMCBL"}
                            request_path = request_path + parse_params_to_str(params)
                            url = API_URL + request_path
                            body = ""
                            sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                            header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                            response = requests.get(url, headers=header)
                            next_ticker = json.loads(response.text)
                            next_eth_price = float(next_ticker['data']['last'])
                            if next_eth_price > 0:
                                w9 = 1 
                            else:
                                w9 = 0
                        next_bod = (next_eth_price - real_eth_price)/ real_eth_price
                        if w4 % 300 == 0:
                            print('正在细微监控价格',str(next_bod) + '====' +str(next_eth_price) +'=====' +str(real_eth_price))
                        time_now = str(datetime.utcnow())[0:19]
                        time_dd_now = time_now[0:10]
                        time_hh_now = time_now[11:16]
                        if next_bod <= 0.02 or time_hh_now == '23:59':
                            print('卖出平多仓',next_eth_price)
                            logo_s = 0
                            while logo_s == 0:
                                time.sleep(1)
                                # 平多
                                timestamp = get_timestamp()
                                response = None
                                clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                                request_path = "/api/mix/v1/order/placeOrder"
                                url = API_URL + request_path
                                params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_long","size":str(buy_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                                body = json.dumps(params)
                                sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                                header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                                response = requests.post(url, data=body, headers=header)
                                sell_res = json.dumps(response.text)
                                sell_id = int(sell_res['data']['orderId'])
                                if int(sell_id)  > 10:
                                    logo_s = 1
                                else:
                                    logo_s = 0
                            del order_list[0]
                            finish_date.append(str(datetime.utcnow())[0:10])
                            print('finish_date',sell_id,finish_date)
                            w2 = 0 
                            p2 = 0
                        elif next_bod >= 0.003:
                            out_order_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
                            out_order_price = str(next_eth_price)
                            time.sleep(60)
                            w5 = 0
                            while len(order_list) > 0:
                                time.sleep(1)
                                w10 = 0 
                                while w10 == 0:
                                    timestamp = get_timestamp()
                                    response = None
                                    request_path = "/api/mix/v1/market/ticker"
                                    url = API_URL + request_path
                                    params = {"symbol":"BTCUSDT_UMCBL"}
                                    request_path = request_path + parse_params_to_str(params)
                                    url = API_URL + request_path
                                    body = ""
                                    sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                                    header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                                    response = requests.get(url, headers=header)
                                    next_ticker_1 = json.loads(response.text)
                                    next_eth_price_1 = float(next_ticker_1['data']['last'])
                                    if next_eth_price_1 > 0:
                                        w10 = 1 
                                    else:
                                        w10 = 0
                                next_bod_1 = (next_eth_price_1 - real_eth_price)/ real_eth_price
                                if w5 % 300 == 0:
                                    print('正在细微监控价格',str(next_bod_1) + '====' +str(next_eth_price_1) +'=====' +str(real_eth_price))
                                time_now = str(datetime.utcnow())[0:19]
                                time_dd_now = time_now[0:10]
                                time_hh_now = time_now[11:16]
                                if next_bod_1 <= 0.003 or time_hh_now == '23:59':
                                    print('卖出平多仓',next_eth_price_1)
                                    logo_s = 0
                                    while logo_s == 0:
                                        time.sleep(1)
                                        # 平多
                                        timestamp = get_timestamp()
                                        response = None
                                        clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                                        request_path = "/api/mix/v1/order/placeOrder"
                                        url = API_URL + request_path
                                        params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_long","size":str(buy_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                                        body = json.dumps(params)
                                        sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                                        header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                                        response = requests.post(url, data=body, headers=header)
                                        sell_res = json.dumps(response.text)
                                        sell_id = int(sell_res['data']['orderId'])
                                        if int(sell_id)  > 10:
                                            logo_s = 1
                                        else:
                                            logo_s = 0
                                    del order_list[0]
                                    finish_date.append(str(datetime.utcnow())[0:10])
                                    print('finish_date',sell_id,finish_date)
                                    w2 = 0 
                                    p2 = 0
                                elif next_bod_1 >= 0.009:
                                    print('卖出平多仓',next_eth_price_1)
                                    logo_s = 0
                                    while logo_s == 0:
                                        time.sleep(1)
                                        # 平多
                                        timestamp = get_timestamp()
                                        response = None
                                        clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                                        request_path = "/api/mix/v1/order/placeOrder"
                                        url = API_URL + request_path
                                        params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_long","size":str(buy_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                                        body = json.dumps(params)
                                        sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                                        header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                                        response = requests.post(url, data=body, headers=header)
                                        sell_res = json.dumps(response.text)
                                        sell_id = int(sell_res['data']['orderId'])
                                        if int(sell_id)  > 10:
                                            logo_s = 1
                                        else:
                                            logo_s = 0
                                    del order_list[0]
                                    finish_date.append(str(datetime.utcnow())[0:10])
                                    print('finish_date',sell_id,finish_date)
                                    w2 = 0 
                                    p2 = 0
                                else:
                                    w5 += 1
                                    continue
                        else:
                            w4 += 1
                            continue
                else:
                    w3 += 1
                    continue
        elif order_type == 2:
            w3 = 0
            while len(order_list)>0:
                time.sleep(1)
                #目前的eth价格
                w7 = 0 
                while w7 == 0:
                    timestamp = get_timestamp()
                    response = None
                    request_path = "/api/mix/v1/market/ticker"
                    url = API_URL + request_path
                    params = {"symbol":"BTCUSDT_UMCBL"}
                    request_path = request_path + parse_params_to_str(params)
                    url = API_URL + request_path
                    body = ""
                    sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                    header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                    response = requests.get(url, headers=header)
                    now_ticker = json.loads(response.text)
                    now_eth_price = float(now_ticker['data']['last'])
                    if now_eth_price > 0:
                        w7 = 1 
                    else:
                        w7 = 0
                bod = (now_eth_price - real_eth_price)/ real_eth_price
                time_now = str(datetime.utcnow())[0:19]
                time_dd = time_now[0:10]
                time_hh = time_now[11:16]
                #Log(time_hh)
                if w3 % 600 ==0:
                    print('正在监控价格',str(bod) + '====' +str(real_eth_price))
                if time_hh == '23:59':
                    print('买入平空仓',now_eth_price)
                    logo_s = 0
                    while logo_s == 0:
                        time.sleep(1)
                        # 平空
                        timestamp = get_timestamp()
                        response = None
                        clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                        request_path = "/api/mix/v1/order/placeOrder"
                        url = API_URL + request_path
                        params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_short","size":str(sell_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                        body = json.dumps(params)
                        sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                        header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                        response = requests.post(url, data=body, headers=header)
                        buy_res = json.dumps(response.text)
                        buy_id = int(buy_res['data']['orderId'])
                        if int(buy_id)  > 10:
                            logo_s = 1
                        else:
                            logo_s = 0
                    del order_list[0]
                    finish_date.append(str(datetime.utcnow())[0:10])
                    print('finish_date',buy_id,finish_date)
                    w2 = 0 
                    p2 = 0                    
                elif bod >= 0.003:
                    print('买出平空仓监控中')
                    time.sleep(3)
                    w8 = 0
                    while w8 == 0:
                        timestamp = get_timestamp()
                        response = None
                        request_path = "/api/mix/v1/market/ticker"
                        url = API_URL + request_path
                        params = {"symbol":"BTCUSDT_UMCBL"}
                        request_path = request_path + parse_params_to_str(params)
                        url = API_URL + request_path
                        body = ""
                        sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                        header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                        response = requests.get(url, headers=header)
                        next_ticker = json.loads(response.text)
                        next_eth_price = float(next_ticker['data']['last'])
                        if next_eth_price > 0:
                            w8 = 1 
                        else:
                            w8 = 0
                    next_bod = (next_eth_price - real_eth_price)/ real_eth_price
                    if next_bod >= 0.003:
                        print('买入平空仓',next_eth_price)
                        logo_s = 0
                        while logo_s == 0:
                            time.sleep(1)
                            # 平空
                            timestamp = get_timestamp()
                            response = None
                            clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                            request_path = "/api/mix/v1/order/placeOrder"
                            url = API_URL + request_path
                            params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_short","size":str(sell_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                            body = json.dumps(params)
                            sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                            header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                            response = requests.post(url, data=body, headers=header)
                            buy_res = json.dumps(response.text)
                            buy_id = int(buy_res['data']['orderId'])
                            if int(buy_id)  > 10:
                                logo_s = 1
                            else:
                                logo_s = 0
                        del order_list[0]
                        finish_date.append(str(datetime.utcnow())[0:10])
                        print('finish_date',buy_id,finish_date)
                        w2 = 0 
                        p2 = 0
                    else:
                        print('回归到正常价格监控中')
                        w3 += 1
                        continue
                elif bod < -0.001:
                    out_order_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
                    out_order_price = str(now_eth_price)
                    time.sleep(60)
                    w4 = 0
                    while len(order_list) > 0:
                        time.sleep(1)
                        w9 = 0 
                        while w9 == 0:
                            timestamp = get_timestamp()
                            response = None
                            request_path = "/api/mix/v1/market/ticker"
                            url = API_URL + request_path
                            params = {"symbol":"BTCUSDT_UMCBL"}
                            request_path = request_path + parse_params_to_str(params)
                            url = API_URL + request_path
                            body = ""
                            sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                            header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                            response = requests.get(url, headers=header)
                            next_ticker = json.loads(response.text)
                            next_eth_price = float(next_ticker['data']['last'])
                            if next_eth_price > 0:
                                w9 = 1 
                            else:
                                w9 = 0
                        next_bod = (next_eth_price - real_eth_price)/ real_eth_price
                        if w4 % 300 == 0:
                            print('正在细微监控价格',str(next_bod) + '====' +str(next_eth_price) +'=====' +str(real_eth_price))
                        time_now = str(datetime.utcnow())[0:19]
                        time_dd_now = time_now[0:10]
                        time_hh_now = time_now[11:13]
                        if next_bod >= -0.001 or time_hh_now == '23:59':
                            print('买入平空仓',next_eth_price)
                            logo_s = 0
                            while logo_s == 0:
                                time.sleep(1)
                                # 平空
                                timestamp = get_timestamp()
                                response = None
                                clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                                request_path = "/api/mix/v1/order/placeOrder"
                                url = API_URL + request_path
                                params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_short","size":str(sell_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                                body = json.dumps(params)
                                sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                                header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                                response = requests.post(url, data=body, headers=header)
                                buy_res = json.dumps(response.text)
                                buy_id = int(buy_res['data']['orderId'])
                                if int(buy_id)  > 10:
                                    logo_s = 1
                                else:
                                    logo_s = 0
                            del order_list[0]
                            finish_date.append(str(datetime.utcnow())[0:10])
                            print('finish_date',buy_id,finish_date)
                            w2 = 0 
                            p2 = 0
                        elif next_bod <= -0.003:
                            out_order_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
                            out_order_price = str(next_eth_price)
                            time.sleep(60)
                            w5 = 0
                            while len(order_list) > 0:
                                time.sleep(1)
                                w10 = 0 
                                while w10 == 0:
                                    timestamp = get_timestamp()
                                    response = None
                                    request_path = "/api/mix/v1/market/ticker"
                                    url = API_URL + request_path
                                    params = {"symbol":"BTCUSDT_UMCBL"}
                                    request_path = request_path + parse_params_to_str(params)
                                    url = API_URL + request_path
                                    body = ""
                                    sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                                    header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                                    response = requests.get(url, headers=header)
                                    next_ticker_1 = json.loads(response.text)
                                    next_eth_price_1 = float(next_ticker_1['data']['last'])
                                    if next_eth_price_1 > 0:
                                        w10 = 1 
                                    else:
                                        w10 = 0
                                next_bod_1 = (next_eth_price_1 - real_eth_price)/ real_eth_price
                                if w5 % 300 == 0:
                                    print('正在细微监控价格',str(next_bod_1) + '====' +str(next_eth_price_1) +'=====' +str(real_eth_price))
                                time_now = str(datetime.utcnow())[0:19]
                                time_dd_now = time_now[0:10]
                                time_hh_now = time_now[11:16]
                                if next_bod_1 >= -0.003 or time_hh_now == '23:59':
                                    print('买入平空仓',next_eth_price_1)
                                    logo_s = 0
                                    while logo_s == 0:
                                        time.sleep(1)
                                        # 平空
                                        timestamp = get_timestamp()
                                        response = None
                                        clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                                        request_path = "/api/mix/v1/order/placeOrder"
                                        url = API_URL + request_path
                                        params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_short","size":str(sell_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                                        body = json.dumps(params)
                                        sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                                        header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                                        response = requests.post(url, data=body, headers=header)
                                        buy_res = json.dumps(response.text)
                                        buy_id = int(buy_res['data']['orderId'])
                                        if int(buy_id)  > 10:
                                            logo_s = 1
                                        else:
                                            logo_s = 0
                                    del order_list[0]
                                    finish_date.append(str(datetime.utcnow())[0:10])
                                    print('finish_date',buy_id,finish_date)
                                    w2 = 0 
                                    p2 = 0
                                elif next_bod_1 <= -0.009:
                                    print('买入平空仓',next_eth_price_1)
                                    logo_s = 0
                                    while logo_s == 0:
                                        time.sleep(1)
                                        # 平空
                                        timestamp = get_timestamp()
                                        response = None
                                        clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                                        request_path = "/api/mix/v1/order/placeOrder"
                                        url = API_URL + request_path
                                        params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_short","size":str(sell_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                                        body = json.dumps(params)
                                        sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                                        header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                                        response = requests.post(url, data=body, headers=header)
                                        buy_res = json.dumps(response.text)
                                        buy_id = int(buy_res['data']['orderId'])
                                        if int(buy_id)  > 10:
                                            logo_s = 1
                                        else:
                                            logo_s = 0
                                    del order_list[0]
                                    finish_date.append(str(datetime.utcnow())[0:10])
                                    print('finish_date',buy_id,finish_date)
                                    w2 = 0 
                                    p2 = 0
                                else:
                                    w5 += 1
                                    continue
                        else:
                            w4 += 1
                            continue
                else:
                    w3 += 1
                    continue
        elif order_type == 3:
            w3 = 0
            while len(order_list)>0:
                time.sleep(1)
                #目前的eth价格
                w7 = 0 
                while w7 == 0:
                    timestamp = get_timestamp()
                    response = None
                    request_path = "/api/mix/v1/market/ticker"
                    url = API_URL + request_path
                    params = {"symbol":"BTCUSDT_UMCBL"}
                    request_path = request_path + parse_params_to_str(params)
                    url = API_URL + request_path
                    body = ""
                    sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                    header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                    response = requests.get(url, headers=header)
                    now_ticker = json.loads(response.text)
                    now_eth_price = float(now_ticker['data']['last'])
                    if now_eth_price > 0:
                        w7 = 1 
                    else:
                        w7 = 0
                bod = (now_eth_price - real_eth_price)/ real_eth_price
                time_now = str(datetime.utcnow())[0:19]
                time_dd = time_now[0:10]
                time_hh = time_now[11:16]
                if w3 % 600 ==0:
                    print('正在监控价格',str(bod) + '====' +str(real_eth_price))
                if time_hh == '23:59':
                    print('买入平空仓',now_eth_price)
                    logo_s = 0
                    while logo_s == 0:
                        time.sleep(1)
                        # 平空
                        timestamp = get_timestamp()
                        response = None
                        clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                        request_path = "/api/mix/v1/order/placeOrder"
                        url = API_URL + request_path
                        params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_short","size":str(sell_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                        body = json.dumps(params)
                        sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                        header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                        response = requests.post(url, data=body, headers=header)
                        buy_res = json.dumps(response.text)
                        buy_id = int(buy_res['data']['orderId'])
                        if int(buy_id)  > 10:
                            logo_s = 1
                        else:
                            logo_s = 0
                    del order_list[0]
                    finish_date.append(str(datetime.utcnow())[0:10])
                    print('finish_date',buy_id,finish_date)
                    w2 = 0 
                    p2 = 0                    
                elif bod >= 0.03:
                    print('买出平空仓监控中')
                    time.sleep(3)
                    w8 = 0
                    while w8 == 0:
                        timestamp = get_timestamp()
                        response = None
                        request_path = "/api/mix/v1/market/ticker"
                        url = API_URL + request_path
                        params = {"symbol":"BTCUSDT_UMCBL"}
                        request_path = request_path + parse_params_to_str(params)
                        url = API_URL + request_path
                        body = ""
                        sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                        header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                        response = requests.get(url, headers=header)
                        next_ticker = json.loads(response.text)
                        next_eth_price = float(next_ticker['data']['last'])
                        if next_eth_price > 0:
                            w8 = 1 
                        else:
                            w8 = 0
                    next_bod = (next_eth_price - real_eth_price)/ real_eth_price
                    if next_bod >= 0.03:
                        print('买入平空仓',next_eth_price)
                        logo_s = 0
                        while logo_s == 0:
                            time.sleep(1)
                            # 平空
                            timestamp = get_timestamp()
                            response = None
                            clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                            request_path = "/api/mix/v1/order/placeOrder"
                            url = API_URL + request_path
                            params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_short","size":str(sell_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                            body = json.dumps(params)
                            sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                            header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                            response = requests.post(url, data=body, headers=header)
                            buy_res = json.dumps(response.text)
                            buy_id = int(buy_res['data']['orderId'])
                            if int(buy_id)  > 10:
                                logo_s = 1
                            else:
                                logo_s = 0
                        del order_list[0]
                        finish_date.append(str(datetime.utcnow())[0:10])
                        print('finish_date',buy_id,finish_date)
                        w2 = 0 
                        p2 = 0
                    else:
                        print('回归到正常价格监控中')
                        w3 += 1
                        continue
                elif bod < -0.02:
                    out_order_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
                    out_order_price = str(now_eth_price)
                    time.sleep(60)
                    w4 = 0
                    while len(order_list) > 0:
                        time.sleep(1)
                        w9 = 0 
                        while w9 == 0:
                            timestamp = get_timestamp()
                            response = None
                            request_path = "/api/mix/v1/market/ticker"
                            url = API_URL + request_path
                            params = {"symbol":"BTCUSDT_UMCBL"}
                            request_path = request_path + parse_params_to_str(params)
                            url = API_URL + request_path
                            body = ""
                            sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                            header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                            response = requests.get(url, headers=header)
                            next_ticker = json.loads(response.text)
                            next_eth_price = float(next_ticker['data']['last'])
                            if next_eth_price > 0:
                                w9 = 1 
                            else:
                                w9 = 0
                        next_bod = (next_eth_price - real_eth_price)/ real_eth_price
                        if w4 % 300 == 0:
                            print('正在细微监控价格',str(next_bod) + '====' +str(next_eth_price) +'=====' +str(real_eth_price))
                        time_now = str(datetime.utcnow())[0:19]
                        time_dd_now = time_now[0:10]
                        time_hh_now = time_now[11:13]
                        if next_bod >= -0.02 or time_hh_now == '23:59':
                            print('买入平空仓',next_eth_price)
                            logo_s = 0
                            while logo_s == 0:
                                time.sleep(1)
                                # 平空
                                timestamp = get_timestamp()
                                response = None
                                clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                                request_path = "/api/mix/v1/order/placeOrder"
                                url = API_URL + request_path
                                params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_short","size":str(sell_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                                body = json.dumps(params)
                                sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                                header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                                response = requests.post(url, data=body, headers=header)
                                buy_res = json.dumps(response.text)
                                buy_id = int(buy_res['data']['orderId'])
                                if int(buy_id)  > 10:
                                    logo_s = 1
                                else:
                                    logo_s = 0
                            del order_list[0]
                            finish_date.append(str(datetime.utcnow())[0:10])
                            print('finish_date',buy_id,finish_date)
                            w2 = 0 
                            p2 = 0
                        elif next_bod <= -0.03:
                            out_order_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
                            out_order_price = str(next_eth_price)
                            time.sleep(60)
                            w5 = 0
                            while len(order_list) > 0:
                                time.sleep(1)
                                w10 = 0 
                                while w10 == 0:
                                    timestamp = get_timestamp()
                                    response = None
                                    request_path = "/api/mix/v1/market/ticker"
                                    url = API_URL + request_path
                                    params = {"symbol":"BTCUSDT_UMCBL"}
                                    request_path = request_path + parse_params_to_str(params)
                                    url = API_URL + request_path
                                    body = ""
                                    sign_cang = sign(pre_hash(timestamp, "GET", request_path, str(body)), API_SECRET_KEY)
                                    header = get_header(API_KEY, sign_cang, timestamp, PASSPHRASE)
                                    response = requests.get(url, headers=header)
                                    next_ticker_1 = json.loads(response.text)
                                    next_eth_price_1 = float(next_ticker_1['data']['last'])
                                    if next_eth_price_1 > 0:
                                        w10 = 1 
                                    else:
                                        w10 = 0
                                next_bod_1 = (next_eth_price_1 - real_eth_price)/ real_eth_price
                                if w5 % 300 == 0:
                                    print('正在细微监控价格',str(next_bod_1) + '====' +str(next_eth_price_1) +'=====' +str(real_eth_price))
                                time_now = str(datetime.utcnow())[0:19]
                                time_dd_now = time_now[0:10]
                                time_hh_now = time_now[11:16]
                                if next_bod_1 >= -0.03 or time_hh_now == '23:59':
                                    print('买入平空仓',next_eth_price_1)
                                    logo_s = 0
                                    while logo_s == 0:
                                        time.sleep(1)
                                        # 平空
                                        timestamp = get_timestamp()
                                        response = None
                                        clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                                        request_path = "/api/mix/v1/order/placeOrder"
                                        url = API_URL + request_path
                                        params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_short","size":str(sell_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                                        body = json.dumps(params)
                                        sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                                        header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                                        response = requests.post(url, data=body, headers=header)
                                        buy_res = json.dumps(response.text)
                                        buy_id = int(buy_res['data']['orderId'])
                                        if int(buy_id)  > 10:
                                            logo_s = 1
                                        else:
                                            logo_s = 0
                                    del order_list[0]
                                    finish_date.append(str(datetime.utcnow())[0:10])
                                    print('finish_date',buy_id,finish_date)
                                    w2 = 0 
                                    p2 = 0
                                elif next_bod_1 <= -0.09:
                                    print('买入平空仓',next_eth_price_1)
                                    logo_s = 0
                                    while logo_s == 0:
                                        time.sleep(1)
                                        # 平空
                                        timestamp = get_timestamp()
                                        response = None
                                        clientoid = "bitget%s"%(str(int(datetime.now().timestamp())))
                                        request_path = "/api/mix/v1/order/placeOrder"
                                        url = API_URL + request_path
                                        params = {"symbol":"BTCUSDT_UMCBL","marginCoin":"USDT","side":"close_short","size":str(sell_num),"orderType":"market","timeInForceValue":"normal","clientOid":clientoid}
                                        body = json.dumps(params)
                                        sign_tranfer = sign(pre_hash(timestamp, "POST", request_path, str(body)), API_SECRET_KEY)
                                        header = get_header(API_KEY, sign_tranfer, timestamp, PASSPHRASE)
                                        response = requests.post(url, data=body, headers=header)
                                        buy_res = json.dumps(response.text)
                                        buy_id = int(buy_res['data']['orderId'])
                                        if int(buy_id)  > 10:
                                            logo_s = 1
                                        else:
                                            logo_s = 0
                                    del order_list[0]
                                    finish_date.append(str(datetime.utcnow())[0:10])
                                    print('finish_date',buy_id,finish_date)
                                    w2 = 0 
                                    p2 = 0
                                else:
                                    w5 += 1
                                    continue
                        else:
                            w4 += 1
                            continue
                else:
                    w3 += 1
                    continue
        else:
            print('发生了未知错误，不能平单')
            time.sleep(1)
            continue
