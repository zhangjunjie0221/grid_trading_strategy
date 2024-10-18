import hashlib
import hmac
import logging
import time
import urllib.parse
import requests
from config.config import proxies
from config.logger import setup_logger


class Binance():
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.binance.com"  
        self.logger = setup_logger('Binance', 'BinanceAPI.log')


    def get_signature(self, params):
        '''生成签名'''
        query_string = urllib.parse.urlencode(params) 
        return hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()  


    def get_account (self):
        '''查询账户'''
        endpoint = "/api/v3/account"  
        data = self.request(endpoint)  
        return data 
    

    def create_order(self, symbol, side, quantity, price=None, order_type='LIMIT_MAKER'):
        '''创建maker订单'''
        endpoint = "/api/v3/order"  
        params = {
            'symbol': symbol,  
            'side': side,  #'BUY'或'SELL'
            'type': order_type,  
            'quantity': quantity,  
        }

        if price is not None:
            params['price'] = price #限价单时

        try:
            response = self.request(endpoint, params=params, method='POST')
            self.logger.info(f'创建订单完成, 订单号为:{response['orderId']}')
            return response['orderId']  # 返回订单 ID
        except Exception as e:
            self.logger.error(f"创建订单过程中发生错误: {e}")


    def get_order_status(self, symbol, order_id):
        '''查询订单状态'''
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol,
            'orderId': order_id
        }

        try:
            response = self.request(endpoint, params=params)
        
            
            #提取策略类里面所需的字段
            status = response['status']
            filled_amount = response['executedQty']
            average_fill_price = response['price']
            order_type = response['side']
            remaining_amount = float(response['origQty']) - float(response['executedQty'])
            
            return {
                'status': status, #订单完成状态
                'filled_amount': filled_amount, #订单交易完成数量
                'average_fill_price': average_fill_price, #订单交易价格
                'order_type': order_type, #订单是买还是卖类型
                'remaining_amount': remaining_amount #订单剩余交易数量
            }

        except Exception as e:
            self.logger.error(f"查询订单状态时发生错误:{e},参数: {params}")


    def cancel_order(self, symbol, order_id):
        '''取消订单''' 
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        try:
            response = self.request(endpoint, params=params, method='DELETE')
            if 'code' in response:
                self.logger.error(f"取消订单失败: {response['msg']}")
            else:
                self.logger.info(f"订单{order_id}已成功取消。")
                return response
        except Exception as e:
            self.logger.error(f"取消订单过程中发生错误: {e}")


    def get_open_orders(self, symbol):
        '''获取未成交订单'''
        endpoint = "/api/v3/openOrders"
        params = {}
        if symbol:
            params['symbol'] = symbol

        try:
            response = self.request(endpoint, params=params)
            return response
        except Exception as e:
            self.logger.error(f"获取未成交订单时发生错误: {e}")
            return []
        

    def request(self, endpoint, params=None, method='GET', retries=3, delay=1):
        '''发送请求'''
        if params is None:
            params = {}  #如果没有传入参数则初始化为空字典

        params['timestamp'] = int(time.time() * 1000)  
        params['signature'] = self.get_signature(params)  
        headers = {
            'X-MBX-APIKEY': self.api_key  
        }
        
        #添加重试机制
        for attempt in range(retries):
            try:
                if method == 'POST':
                    response = requests.post(f"{self.base_url}{endpoint}", headers=headers, params=params , proxies=proxies)  
                elif method == 'GET': 
                    response = requests.get(f"{self.base_url}{endpoint}", headers=headers, params=params, proxies=proxies)
                elif method == 'DELETE':  
                    response = requests.delete(f"{self.base_url}{endpoint}", headers=headers, params=params, proxies=proxies)

                return response.json()
            except requests.exceptions.RequestException as e:
                self.logger.error(f"请求 {method} {endpoint} 时发生错误: {e}")
                time.sleep(delay)
