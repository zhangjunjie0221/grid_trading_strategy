import hashlib
import hmac
import logging
import time
import urllib.parse
import redis
import requests
from config.config import proxies ,REDIS_CONFIG
from config.logger import setup_logger
from utils.ding_ding import DingDing


class Binance():
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.binance.com"  
        self.logger = setup_logger('Binance', 'BinanceAPI.log')
        self.redis_client = redis.Redis(host=REDIS_CONFIG['host'], port=REDIS_CONFIG['port'], db=REDIS_CONFIG['db'],password=REDIS_CONFIG['password'])
        self.dingding = DingDing() 


    def get_signature(self, params):
        '''生成签名'''
        query_string = urllib.parse.urlencode(params) 
        return hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()  


    def get_account (self):
        '''查询账户'''
        endpoint = "/api/v3/account"  
        data = self.request(endpoint)  

        usdc_balance = 0
        usdt_balance = 0
        
        for asset in data['balances']:
            if asset['asset'] == 'USDC':
                usdc_balance = float(asset['free'])
            elif asset['asset'] == 'USDT':
                usdt_balance = float(asset['free'])
        
        #存放到Redis
        self.redis_client.set('usdc_balance', usdc_balance)
        self.redis_client.set('usdt_balance', usdt_balance) 
    

    def create_order(self, symbol, side, quantity, price=None, order_type='LIMIT_MAKER',timeInForce =None):
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
        if timeInForce is not None:
            params['timeInForce'] = timeInForce

        try:
            response = self.request(endpoint, params=params, method='POST')
            self.logger.debug(response)
            self.logger.debug(f'创建订单完成, 订单号为:{response['orderId']}')
            return response['orderId']  # 返回订单 ID
        except Exception as e:
            if response['code'] == -2010:
                self.logger.debug(response)
                self.logger.debug("订单会立即成交，请调整价格。")
            elif response['code'] == -1013:
                self.logger.debug(response)
                self.logger.debug("订单金额低于最小要求，请调整数量或价格")
            else :
                self.logger.debug(response)
                self.logger.debug("创建订单的时候发生错误")
                self.dingding.send_alert(f"出现未知错误 ，请处理：{response}")


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
            filled_amount = float(response['executedQty'])
            orig_amount = float(response['origQty'])
            average_fill_price = float(response['price'])
            order_type = response['side']
            remaining_amount = float(response['origQty']) - float(response['executedQty'])
            
            return {
                'status': status, #订单完成状态
                'filled_amount': filled_amount, #订单交易完成数量
                'orig_amount': orig_amount ,#原始订单数量
                'average_fill_price': average_fill_price, #订单交易价格
                'order_type': order_type, #订单是买还是卖类型
                'remaining_amount': remaining_amount #订单剩余交易数量
            }

        except Exception as e:
            self.logger.debug(response)
            self.logger.debug(f"查询订单状态时发生错误:{e},参数: {params}")
            self.dingding.send_alert(f"出现未知错误 ，请处理：{response}")


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
                self.logger.debug(f"取消订单失败: {response['msg']}")
            else:
                self.logger.debug(f"订单{order_id}已成功取消。")
                return response
        except Exception as e:
            self.logger.debug(response)
            self.logger.debug(f"取消订单过程中发生错误: {e}")
            self.dingding.send_alert(f"出现未知错误 ，请处理：{response}")


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
            self.logger.debug(response)
            self.logger.debug("获取未成交订单的时候发生错误")
            self.logger.debug(f"获取未成交订单时发生错误: {e}")
            return []
        

    def request(self, endpoint, params=None, method='GET'):
        '''发送请求'''
        if params is None:
            params = {}  #如果没有传入参数则初始化为空字典

        params['timestamp'] = int(time.time() * 1000)  
        params['signature'] = self.get_signature(params)  
        headers = {
            'X-MBX-APIKEY': self.api_key  
        }
        
        try:
            if method == 'POST':
                response = requests.post(f"{self.base_url}{endpoint}", headers=headers, params=params , proxies=proxies)  
            elif method == 'GET': 
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers, params=params, proxies=proxies)
            elif method == 'DELETE':  
                response = requests.delete(f"{self.base_url}{endpoint}", headers=headers, params=params, proxies=proxies)

            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.debug(response)
            self.logger.debug(f"请求 {method} {endpoint} 时发生错误: {e}")
            self.dingding.send_alert(f"出现未知错误 ，请处理：{response}")

