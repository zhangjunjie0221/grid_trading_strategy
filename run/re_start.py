import redis
from strategy.risk_control import RiskControl
from clients.binance_api import Binance
from config.config import REDIS_CONFIG ,API_KEY, API_SECRET
from utils.ding_ding import DingDing

class Restart:
    def re_start(self):
        redis_client = redis.Redis(host=REDIS_CONFIG['host'], port=REDIS_CONFIG['port'], db=REDIS_CONFIG['db'],password=REDIS_CONFIG['password'])
        dingding = DingDing()
        api_client = Binance(API_KEY, API_SECRET) 


        open_orders = api_client.get_open_orders("USDCUSDT")
        for order in open_orders:
            api_client.cancel_order(order['symbol'], order['orderId'])
        api_client.get_account()
        usdc_balance = redis_client.get('usdc_balance')
        usdt_balance = redis_client.get('usdt_balance')
        usdc_balance = float(usdc_balance)
        usdt_balance = float(usdt_balance)
        order_id = []
        boolean = True
        if usdc_balance <40 :
            id = api_client.create_order("USDCUSDT","BUY",int(40-usdc_balance)+1,order_type="MARKET")
            order_id.append(id)
        elif usdt_balance < 40:
            id = api_client.create_order("USDCUSDT","SELL",40-usdt_balance,order_type="MARKET")
            order_id.append(id)
        elif usdt_balance < 40 and usdc_balance <40:
            open_orders = api_client.get_open_orders("USDCUSDT")
            for order in open_orders:
                api_client.cancel_order(order['symbol'], order['orderId'])
            dingding.send_alert('资产异常 系统停止')

        
        while boolean :
            for id in order_id :
                data = api_client.get_order_status("USDCUSDT",id)
                if data['status'] == 'FILLED':
                    boolean = False
        
        dingding.send_alert('系统重置完成')

if __name__ == "__main__":
    restart = Restart()
    restart.re_start()

    