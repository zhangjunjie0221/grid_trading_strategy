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
        self.retry_count = 0  
        self.max_retries = 3    

    
    def close(self):
        '''关闭数据库'''
        self.database.mongo_client.close()
    

    def create_maker_order(self, pair, amount, price, order_type='BUY'):
        '''创建订单'''
        try:
            order_id = self.api_client.create_order(pair, order_type, amount, price)
            if order_id:
                self.database.store_order_id(order_id)  #存入MongoDB
                self.logger.debug(f"已创建 {'买入' if order_type == 'BUY' else '卖出'} 订单，价格: {price}，数量: {amount}, 订单ID: {order_id}")
                self.dingding.send_alert(f"已创建 {'买入' if order_type == 'BUY' else '卖出'} 订单，价格: {price}，数量: {amount}, 订单ID: {order_id}")
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

                yield bid, ask
            else:
                break


    def first_create_orders(self):
        '''初始化订单'''
        order_type_buy = 'BUY'
        order_type_sell = 'SELL'

        for price, amount in self.buy_orders.items():
            self.create_maker_order(self.pairs,amount,price,order_type_buy)

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
                    self.first_create_orders()
                    initialized_orders = True

                #获取遍历当前订单的信息状态
                for order_id in self.database.get_all_order_ids():
                    data = self.check_order_status(order_id)
                    status = data['status'] #订单完成状态
                    filled_amount = data['filled_amount'] #订单成交数量
                    orig_amount = data['orig_amount'] #原始订单数量
                    average_fill_price = data['average_fill_price'] #订单成交价格
                    order_type = data['order_type'] #订单的买卖类型
                    remaining_amount = data['remaining_amount'] #订单交易剩余的数量

                
                    if bid_price <= 1 and order_type == 'SELL' and status == 'FILLED':
                        self.create_maker_order(self.pairs,orig_amount,average_fill_price,order_type)
                        id = self.create_maker_order(self.pairs,orig_amount,1.0000,"BUY")
                        self.database.remove_order_id(id)
                        self.database.remove_order_id(order_id)

                    
                    if ask_price > 1 and order_type == 'BUY'and status == 'FILLED':
                        self.create_maker_order(self.pairs,orig_amount,average_fill_price,order_type)
                        id = self.create_maker_order(self.pairs,orig_amount,1.0000,"SELL")
                        self.database.remove_order_id(id)
                        self.database.remove_order_id(order_id)


                        
                    




                #     if order_type == 'BUY':
                #         buy_amount += filled_amount
                #         for price , amount in buy_orders.items():
                #             if average_fill_price == price:
                #                 buy_orders[price] += remaining_amount
                    
                #     if order_type == 'SELL':
                #         sell_amount += filled_amount
                #         for price , amount in sell_orders.items():
                #             if average_fill_price == price:
                #                 buy_orders[price] += remaining_amount
                
                # for price , amount in self.buy_orders.items():
                #     collection = []
                #     if price in buy_orders:
                #         #获取当前的数量
                #         current_amount = buy_orders[price]
                #         #获取初始的数量
                #         available_amount = self.buy_orders[price]

                #         if current_amount > available_amount:
                #             buy_orders[price] = self.buy_orders[price]
                #             for price_second , amount_second in buy_orders.items():
                #                 if price_second < price :
                #                     collection.append(price)
                #             for price_third in sorted(collection):
                #                 if (buy_orders[price_third] + (current_amount - self.buy_orders[price])) >= self.buy_orders[price_third]:
                #                     buy_orders[price_third] = self.buy_orders[price_third]
                                
                #         elif current_amount < available_amount:
                #             buy_orders[price] = current_amount

                #         elif current_amount == available_amount:
                #             buy_orders[price] = self.buy_orders[price]
                

                        



                # if buy_amount != sell_amount: 
                #     different = abs(buy_amount-sell_amount)
                #     if (buy_amount-sell_amount) < 0 :
                #         pass
                
                



                #     if status == 'FILLED' and order_type == 'BUY':
                #         print(f"买入订单 {order_id} 已完成")
                #         #再提升价格卖单
                #         take_profit_price = average_fill_price + self.step
                #         sell_amount = int(filled_amount)
                #         self.create_maker_order(self.pairs, sell_amount, take_profit_price, order_type='SELL')
                #         self.database.remove_order_id(order_id)

                #     elif status == 'PARTIALLY_FILLED' and order_type == 'BUY':
                #         print(f"买入订单 {order_id} 部分成交，已成交: {filled_amount}，剩余: {remaining_amount}")

                #     elif status == 'FILLED' and order_type == 'SELL':
                #         print(f"卖出订单{order_id}已完成")
                #         buy_price = 0
                #         buy_amount = 0
                #         boolean = True #新增限制条件 用于后面判定网格区间是否还存在订单 防止在一个区间重复下单

                #         #判断如果当前的市场价的买入价格 小于 之前的买入订单的价格 则选择下 价格为当前市场价格的买入单和对应的数量 
                #         if bid_price < average_fill_price - self.step :

                #             #判断马上要下买单的价格区间 是否存在 在现有未完全成交的买单中 防止在一个区间重复下单
                #             for order_id in self.orders_id: 
                #                 if self.check_order_status(order_id)['order_type'] == 'BUY' and self.check_order_status(order_id)['status'] == 'PARTIALLY_FILLED' :
                #                     fill_price = self.check_order_status(order_id)['average_fill_price']
                #                     if bid_price == fill_price:
                #                         #如果有则把变量boolean改为false
                #                         boolean = False
                #                         break
                #             #如果boolean值是true则可以进行下一步赋值 否则跳过下面赋值步骤
                #             if boolean:
                #                 #判断要下单的价格是否在我们规定的网格内 如果在则可以赋值 
                #                 for price, quantity in self.orders.items():
                #                     if price == bid_price:
                #                         buy_price = bid_price
                #                         buy_amount = int(round(quantity / price, 5))

                #         #如果当前的市场价的买入价格 大于等于 之前的买入订单的价格 则选择下 价格为之前的买入订单的价格和对应的数量 
                #         buy_price = average_fill_price - self.step
                #         #判断要下单的价格是否在我们规定的网格内 如果在则可以赋值 
                #         for price, quantity in self.orders.items():
                #             if price == (average_fill_price - self.step):
                #                 buy_amount = int(round(quantity / price, 5))
                        
                #         self.create_maker_order(self.pairs , buy_amount, buy_price , order_type='BUY')
                #         self.database.remove_order_id(order_id)

                #     elif status == 'PARTIALLY_FILLED' and order_type == 'SELL':
                #         print(f"卖出订单{order_id}部分成交，已成交:{filled_amount}，剩余:{remaining_amount} ,继续等待买单完成")

                #     elif status == 'CANCELED':
                #         self.database.remove_order_id(order_id)
            
                # time.sleep(1)  # 每1秒检查一次

        except Exception as e:
            self.logger.debug(f"逻辑交易过程中发生错误: {e}")
            self.retry_count += 1  # 增加重连计数
            if self.retry_count > self.max_retries:
                self.logger.debug("达到最大重连次数，停止尝试。")
            else:
                self.logger.debug("网络波动，尝试重新接入...")
                self.Logical_trading() 
        
        self.close()  #确保在结束时关闭连接

