import logging
import time
import redis
from clients.binance_api import Binance
from config.logger import setup_logger
from config.config import API_KEY , API_SECRET , MIN_ASSET , TradingPair , REDIS_CONFIG
from config.mongodb import Database

class RiskControl:
    def __init__(self):
        self.binance = Binance(API_KEY, API_SECRET)
        self.min_asset = MIN_ASSET
        self.symbol = TradingPair.USDCUSDT.value
        self.logger = setup_logger('RiskControl', 'RiskControl.log')
        self.database = Database()
        self.redis_client = redis.Redis(host=REDIS_CONFIG['host'], port=REDIS_CONFIG['port'], db=REDIS_CONFIG['db'],password=REDIS_CONFIG['password'])


    def get_total_asset(self):
        '''获取总资产'''
        try:
            self.binance.get_account()
            usdc_balance = self.redis_client.get('usdc_balance')
            usdt_balance = self.redis_client.get('usdt_balance')
            usdc_balance = float(usdc_balance)
            usdt_balance = float(usdt_balance)
            open_orders = self.binance.get_open_orders(self.symbol)
            for order in open_orders:
                if order['side']=='BUY':
                    usdc_balance += float(order['origQty'])
                if order['side']=='SELL':
                    usdt_balance += float(order['origQty'])
            total_asset_value = usdc_balance + usdt_balance
            self.logger.debug(f"当前资产总值: {total_asset_value}")
            return total_asset_value
        except Exception as e:
            self.logger.debug(f"获取总资产时发生错误: {e}")
            return None


    def monitor_assets(self):
        '''监控资产 如果资产低于阈值 则停止所有交易'''
        while True:
            try:
                total_asset = self.get_total_asset()

                if total_asset is None:  
                    self.logger.debug("无法获取总资产，停止交易。")
                    self.stop_trading()
                    break

                if total_asset < self.min_asset:
                    self.logger.debug(f'当前的资产总值为：{total_asset}，低于设定的最小风控值。')
                    self.stop_trading()
                    break
                time.sleep(5)
            except Exception as e:
                self.logger.debug(f"监控资产时发生错误: {e}")


    def stop_trading(self):
        '''取消所有订单操作'''
        self.logger.debug("正在取消所有未成交的订单...")
        self.cancel_all_orders()
        self.logger.debug("交易已停止。")


    def cancel_all_orders(self):
        '''调用api方法取消订单'''
        try:
            orders = self.binance.get_open_orders(self.symbol)
            for order in orders:
                self.binance.cancel_order(order['symbol'], order['orderId'])
                self.database.remove_order_id(order['orderId'])
                self.logger.debug(f"订单 {order['orderId']} 已取消。")
        except Exception as e:
            self.logger.debug(f"取消未成交订单时发生错误: {e}")