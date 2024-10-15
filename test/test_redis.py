import redis
import pickle

class test_get_market_prices:
    def __init__(self, redis_host='localhost', redis_port=6379):
        
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port)

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

if __name__ == "__main__":
    fetcher = test_get_market_prices()
    for bids, asks in fetcher.get_market_prices():
        print(f"Bids: {bids}, Asks: {asks}")