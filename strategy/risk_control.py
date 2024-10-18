import logging
import time
from clients.binance_api import Binance
from config.logger import setup_logger
from config.config import API_KEY , API_SECRET , MIN_ASSET , TradingPair
from config.mongodb import Database

class RiskControl:
    def __init__(self):
        self.binance = Binance(API_KEY, API_SECRET)
        self.min_asset = MIN_ASSET
        self.symbol = TradingPair.USDCUSDT.value
        self.logger = setup_logger('RiskControl', 'RiskControl.log')
        self.database = Database()


    def get_total_asset(self):
        '''获取总资产'''
        try:
            account_info = self.binance.get_account()
            usdc = next((float(item['free']) for item in account_info['balances'] if item['asset'] == 'USDC'), 0.0)
            usdt = next((float(item['free']) for item in account_info['balances'] if item['asset'] == 'USDT'), 0.0)
            open_orders = self.binance.get_open_orders(self.symbol)
            total_value_of_open_orders = sum(float(order['origQty']) * float(order['price']) for order in open_orders)
            total_asset_value = usdc + usdt + total_value_of_open_orders
            self.logger.info(f"当前资产总值: {total_asset_value}")
            return total_asset_value
        except Exception as e:
            self.logger.error(f"获取总资产时发生错误: {e}")
            return None


    def monitor_assets(self):
        '''监控资产 如果资产低于阈值 则停止所有交易'''
        while True:
            try:
                total_asset = self.get_total_asset()

                if total_asset is None:  
                    self.logger.error("无法获取总资产，停止交易。")
                    print("由于无法获取总资产，停止交易。")
                    self.stop_trading()
                    break

                if total_asset < self.min_asset:
                    self.logger.warning(f'当前的资产总值为：{total_asset}，低于设定的最小风控值。')
                    print("由于资产低于设定值，停止交易。")
                    self.stop_trading()
                    break
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"监控资产时发生错误: {e}")


    def stop_trading(self):
        '''取消所有订单操作'''
        self.logger.info("正在取消所有未成交的订单...")
        self.cancel_all_orders()
        self.logger.info("交易已停止。")


    def cancel_all_orders(self):
        '''调用api方法取消订单'''
        try:
            orders = self.binance.get_open_orders(self.symbol)
            for order in orders:
                self.binance.cancel_order(order['symbol'], order['orderId'])
                self.database.remove_order_id(order)
                self.logger.info(f"订单 {order['orderId']} 已取消。")
        except Exception as e:
            self.logger.error(f"取消未成交订单时发生错误: {e}")