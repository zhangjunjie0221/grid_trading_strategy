import pickle
import time
import redis
from clients.binance_api import Binance
from config.config import STEP , ORDERS , REDIS_CONFIG ,API_KEY ,API_SECRET , TradingPair 
from config.mongodb import Database 
from config.logger import setup_logger


class Strategy:
    def __init__(self):
        self.pairs = TradingPair.USDCUSDT
        self.step = STEP
        self.redis_client = redis.Redis(host=REDIS_CONFIG['host'], port=REDIS_CONFIG['port'], db=REDIS_CONFIG['db'],password=REDIS_CONFIG['password'])
        self.api_client = Binance(API_KEY, API_SECRET)
        self.orders = ORDERS
        self.logger = setup_logger('Strategy', 'Strategy.log')
        self.database = Database()    

    
    def close(self):
        '''关闭数据库'''
        self.database.mongo_client.close()
    

    def create_maker_order(self, pair, amount, price, order_type='BUY'):
        '''创建订单'''
        try:
            order_id = self.api_client.create_order(pair, order_type, amount, price)
            if order_id:
                self.database.store_order_id(order_id)  #存入MongoDB
                self.logger.info(f"已创建 {'买入' if order_type == 'BUY' else '卖出'} 订单，价格: {price}，数量: {amount}, 订单ID: {order_id}")
                return order_id
        except Exception as e:
            self.logger.error(f"创建订单时发生错误: {e}")
            return None

    
    def check_order_status(self, order_id):
        '''检查订单状态'''
        try:
            status = self.api_client.get_order_status(order_id)
            self.logger.info(f"订单 {order_id} 状态: {status['status']}")
            return status
        except Exception as e:
            self.logger.error(f"检查订单状态时发生错误: {e}")
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
                yield bids, asks
            else:
                break


    def first_create_orders(self):
        '''初始化订单'''
        for price, amount in self.orders.items():
            order_type = 'BUY' 

            #当第一次交易的时候 如果价格大于一的话 说明都是需要在元价格的基础上减去一个间隔价格去买 然后 后面再在原价格上去卖
            if price > 1:
                asset_num = round(amount / (price - self.step), 5) 
            
            #如果小于1的话 说明按网格规定的价格买 卖的时候需要加一个价格间隔去卖
            asset_num = round(amount / price, 5)
            self.create_maker_order(self.pairs ,price, asset_num, order_type)



    def Logical_trading(self):
        '''逻辑交易'''
        self.first_create_orders()
        
        try:
            for bid_price, ask_price in self.get_market_prices():
                print(f"当前 Bid: {bid_price}, Ask: {ask_price}")

                #获取遍历当前订单的信息状态
                for order_id in self.database.get_all_order_ids():
                    data = self.check_order_status(order_id)
                    status = data['status'] #订单完成状态
                    filled_amount = data['filled_amount'] #订单成交数量
                    average_fill_price = data['average_fill_price'] #订单成交价格
                    order_type = data['order_type'] #订单的买卖类型
                    remaining_amount = data['remaining_amount'] #订单交易剩余的数量

                    if status == 'FILLED' and order_type == 'BUY':
                        print(f"买入订单 {order_id} 已完成")
                        #再提升价格卖单
                        take_profit_price = average_fill_price + self.step
                        sell_amount = filled_amount
                        self.create_maker_order(self.pairs, sell_amount, take_profit_price, order_type='SELL')
                        self.database.remove_order_id(order_id)

                    elif status == 'PARTIALLY_FILLED' and order_type == 'BUY':
                        print(f"买入订单 {order_id} 部分成交，已成交: {filled_amount}，剩余: {remaining_amount}")

                    elif status == 'FILLED' and order_type == 'SELL':
                        print(f"卖出订单{order_id}已完成")
                        buy_price = 0
                        buy_amount = 0
                        boolean = True #新增限制条件 用于后面判定网格区间是否还存在订单 防止在一个区间重复下单

                        #判断如果当前的市场价的买入价格 小于 之前的买入订单的价格 则选择下 价格为当前市场价格的买入单和对应的数量 
                        if bid_price < average_fill_price - self.step :

                            #判断马上要下买单的价格区间 是否存在 在现有未完全成交的买单中 防止在一个区间重复下单
                            for order_id in self.orders_id: 
                                if self.check_order_status(order_id)['order_type'] == 'BUY' and self.check_order_status(order_id)['status'] == 'PARTIALLY_FILLED' :
                                    fill_price = self.check_order_status(order_id)['average_fill_price']
                                    if bid_price == fill_price:
                                        #如果有则把变量boolean改为false
                                        boolean = False
                                        break
                            #如果boolean值是true则可以进行下一步赋值 否则跳过下面赋值步骤
                            if boolean:
                                #判断要下单的价格是否在我们规定的网格内 如果在则可以赋值 
                                for price, quantity in self.orders.items():
                                    if price == bid_price:
                                        buy_price = bid_price
                                        buy_amount = round(quantity / price, 5)

                        #如果当前的市场价的买入价格 大于等于 之前的买入订单的价格 则选择下 价格为之前的买入订单的价格和对应的数量 
                        buy_price = average_fill_price - self.step
                        #判断要下单的价格是否在我们规定的网格内 如果在则可以赋值 
                        for price, quantity in self.orders.items():
                            if price == (average_fill_price - self.step):
                                buy_amount = round(quantity / price, 5)
                        
                        self.create_maker_order(self.pairs , buy_amount, buy_price , order_type='BUY')
                        self.database.remove_order_id(order_id)

                    elif status == 'PARTIALLY_FILLED' and order_type == 'SELL':
                        print(f"卖出订单{order_id}部分成交，已成交:{filled_amount}，剩余:{remaining_amount} ,继续等待买单完成")
            
                time.sleep(0.1)  # 每0.1秒检查一次

        except Exception as e:
            self.logger.error(f"逻辑交易过程中发生错误: {e}")
        finally:
            self.close()  #确保在结束时关闭连接

