import pickle
import time
import redis
from clients.binance_api import Binance
from config.config import STEP , BUY_ORDERS , SELL_ORDERS , REDIS_CONFIG ,API_KEY ,API_SECRET , TradingPair 
from config.mongodb import Database 
from config.logger import setup_logger
from utils.ding_ding import DingDing


class Strategy:
    def __init__(self):
        self.pairs = TradingPair.USDCUSDT.value
        self.step = STEP
        self.redis_client = redis.Redis(host=REDIS_CONFIG['host'], port=REDIS_CONFIG['port'], db=REDIS_CONFIG['db'],password=REDIS_CONFIG['password'])
        self.api_client = Binance(API_KEY, API_SECRET)
        self.buy_orders = BUY_ORDERS
        self.sell_orders = SELL_ORDERS
        self.logger = setup_logger('Strategy', 'Strategy.log')
        self.database = Database()
        self.dingding = DingDing()    

    
    def close(self):
        '''关闭数据库'''
        self.database.mongo_client.close()
    

    def create_maker_order(self, pair, amount, price, order_sid='BUY',order_type ="LIMIT_MAKER",time_in_force=None):
        '''创建订单'''
        try:
            order_id = self.api_client.create_order(pair, order_sid, amount, price,order_type,time_in_force)
            if order_id:
                self.database.store_order_id(order_id)  #存入MongoDB
                self.logger.debug(f"已创建 {'买入' if order_sid == 'BUY' else '卖出'} 订单，价格: {price}，数量: {amount}, 订单ID: {order_id}")
                self.dingding.send_alert(f"已创建 {'买入' if order_sid == 'BUY' else '卖出'} 订单，价格: {price}，数量: {amount}, 订单ID: {order_id}")
                return order_id
        except Exception as e:
            self.logger.debug(f"创建订单时发生错误: {e}")
            return None

    
    def check_order_status(self, order_id):
        '''检查订单状态'''
        try:
            status = self.api_client.get_order_status(self.pairs,order_id)
            return status
        except Exception as e:
            self.logger.debug(f"检查订单状态时发生错误: {e}")
            return {}


    def get_market_prices(self):
        '''获取市场深度数据'''
        while True:
            message = self.redis_client.brpop('b-depth', timeout=5) #设置超时
            if message:
                data = pickle.loads(message[1])
                market_data = data['data'][0] 
                bids = market_data['bids']
                asks = market_data['asks']
                # 转换为浮点数
                bids_float = [(float(price), float(quantity)) for price, quantity in bids]
                asks_float = [(float(price), float(quantity)) for price, quantity in asks]

                bid = bids_float[0]
                ask = asks_float[0]

                yield bid[0], ask[0]
            else:
                break


    def first_create_orders(self , bid , ask):
        '''初始化订单'''
        order_type_buy = 'BUY'
        order_type_sell = 'SELL'

        if bid < 1:
            for price, amount in self.buy_orders.items():
                if price > bid:
                    self.create_maker_order(self.pairs,amount,price,order_type_buy,order_type="LIMIT" , time_in_force='GTC')
                elif price == bid:
                    self.create_maker_order(self.pairs,amount,price,order_type_buy)
                elif price < bid:
                    self.create_maker_order(self.pairs,amount,price,order_type_buy)
        elif bid >= 1:
            for price, amount in self.buy_orders.items():
                self.create_maker_order(self.pairs,amount,price,order_type_buy)

        if ask > 1:        
            for price, amount in self.sell_orders.items():
                if price < ask:
                    self.create_maker_order(self.pairs,amount,price,order_type_sell,order_type="LIMIT", time_in_force='GTC')
                elif price == ask:
                    self.create_maker_order(self.pairs,amount,price,order_type_sell)
                elif price > ask:
                    self.create_maker_order(self.pairs,amount,price,order_type_sell)
        elif ask <= 1:
            for price, amount in self.sell_orders.items():
                self.create_maker_order(self.pairs,amount,price,order_type_sell)

    def Logical_trading(self):
        '''逻辑交易'''
        #清空消息队列
        self.redis_client.delete('b-depth')
        initialized_orders = False
        
        try:
            for bid_price, ask_price in self.get_market_prices():
                #第一次初始化订单
                if not initialized_orders:
                    self.first_create_orders(bid_price,ask_price)
                    initialized_orders = True

                ids_by_sell = set([])
                ids_by_buy = set([])

                #获取遍历当前订单的信息状态
                for order_id in self.database.get_all_order_ids():
                    data = self.check_order_status(order_id)
                    status = data['status'] #订单完成状态
                    filled_amount = data['filled_amount'] #订单成交数量
                    orig_amount = data['orig_amount'] #原始订单数量
                    average_fill_price = data['average_fill_price'] #订单成交价格
                    order_type = data['order_type'] #订单的买卖类型
                    remaining_amount = data['remaining_amount'] #订单交易剩余的数量

                    if ask_price > 1 and order_type == 'SELL':
                        if ask_price != average_fill_price and status == 'FILLED':
                            self.dingding.send_alert(f'卖单完成 价格: {average_fill_price}，卖出数量: {filled_amount}, 订单ID: {order_id}')
                            id = self.create_maker_order(self.pairs,orig_amount,1.0000,"BUY")
                            ids_by_sell.add(order_id)
                            self.database.remove_order_id(order_id)
                            self.database.remove_order_id(id)
                        elif ask_price == average_fill_price and status != 'PARTIALLY_FILLED':
                            self.dingding.send_alert(f'卖单部分完成 准备cancel掉  价格: {average_fill_price}，卖出数量: {filled_amount}, 订单ID: {order_id}')
                            id = self.create_maker_order(self.pairs,filled_amount,1.0000,"BUY")
                            ids_by_sell.add(order_id)
                            self.database.remove_order_id(order_id)
                            self.database.remove_order_id(id)
                            self.api_client.cancel_order(order_id)
                        elif ask_price == average_fill_price and status == 'FILLED':
                            self.dingding.send_alert(f'卖单完成 价格: {average_fill_price}，卖出数量: {filled_amount}, 订单ID: {order_id}')
                            id = self.create_maker_order(self.pairs,orig_amount,1.0000,"BUY")
                            ids_by_sell.add(order_id)
                            self.database.remove_order_id(order_id)
                            self.database.remove_order_id(id)

                    if bid_price < 1 and order_type == 'BUY':
                        if bid_price != average_fill_price and status == 'FILLED':
                            self.dingding.send_alert(f'买单完成 价格: {average_fill_price}，买入数量: {filled_amount}, 订单ID: {order_id}')
                            id = self.create_maker_order(self.pairs,orig_amount,1.0000,"SELL")
                            ids_by_buy.add(order_id)
                            self.database.remove_order_id(order_id)
                            self.database.remove_order_id(id)
                        elif bid_price == average_fill_price and status == 'PARTIALLY_FILLED':
                            self.dingding.send_alert(f'买单部分完成 准备cancel掉 价格: {average_fill_price}，买入数量: {filled_amount}, 订单ID: {order_id}')
                            id = self.create_maker_order(self.pairs,filled_amount,1.0000,"SELL")
                            ids_by_buy.add(order_id)
                            self.database.remove_order_id(order_id)
                            self.database.remove_order_id(id)
                            self.api_client.cancel_order(order_id)
                        elif bid_price == average_fill_price and status == 'FILLED':
                            self.dingding.send_alert(f'买单完成 价格: {average_fill_price}，买入数量: {filled_amount}, 订单ID: {order_id}')
                            id = self.create_maker_order(self.pairs,orig_amount,1.0000,"SELL")
                            ids_by_buy.add(order_id)
                            self.database.remove_order_id(order_id)
                            self.database.remove_order_id(id)


                if ask_price == 1.0000 and ids_by_sell:
                    for id in ids_by_sell:
                        data = self.check_order_status(id)
                        status = data['status'] #订单完成状态
                        filled_amount = data['filled_amount'] #订单成交数量
                        orig_amount = data['orig_amount'] #原始订单数量
                        average_fill_price = data['average_fill_price'] #订单成交价格
                        order_type = data['order_type'] #订单的买卖类型
                        remaining_amount = data['remaining_amount'] #订单交易剩余的数量
                        self.create_maker_order(self.pairs,orig_amount,average_fill_price,"SELL")
                        self.database.remove_order_id(order_id)
                    ids_by_sell.clear()
                
                if bid_price == 1.0000 and ids_by_buy:
                    for id in ids_by_buy:
                        data = self.check_order_status(id)
                        status = data['status'] #订单完成状态
                        filled_amount = data['filled_amount'] #订单成交数量
                        orig_amount = data['orig_amount'] #原始订单数量
                        average_fill_price = data['average_fill_price'] #订单成交价格
                        order_type = data['order_type'] #订单的买卖类型
                        remaining_amount = data['remaining_amount'] #订单交易剩余的数量
                        self.create_maker_order(self.pairs,orig_amount,average_fill_price,"BUY")
                        self.database.remove_order_id(order_id)
                    ids_by_buy.clear()
            
                time.sleep(1)  # 每1秒检查一次

        except Exception as e:
            self.logger.debug(f"逻辑交易过程中发生错误: {e}") 
            self.dingding.send_alert(f"出现未知错误 ，请处理：{e}")
        
        self.close()  #确保在结束时关闭连接

