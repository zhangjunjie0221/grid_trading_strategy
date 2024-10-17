import json
import pickle
from websocket import create_connection
import ssl
import sys
import time
import traceback
import redis
import logging
from config.config import proxies , REDIS_CONFIG


class MarketData():
    def __init__(self, instrument):
        self.instrument = instrument
        self.lasttime = {instrument.upper(): time.time()}
        self.redis = redis.Redis(host=REDIS_CONFIG['host'], port=REDIS_CONFIG['port'], db=REDIS_CONFIG['db'],password=REDIS_CONFIG['password'])
        self.logger = logging.getLogger('MarketDataFetcher')
        logging.basicConfig(level=logging.INFO)

    def market_data(self):
        ws = None
        st = f'/{self.instrument}@depth20@1000ms'  
        self.lasttime[self.instrument.upper()] = time.time()
        ws_url = f"wss://stream.binance.com:9443/stream?streams={st[1:]}"
        print(ws_url)

        while True:
            try:
                ws = create_connection(ws_url,proxies=proxies,sslopt={"cert_reqs": ssl.CERT_NONE})
                break
            except Exception:
                self.logger.error('Binance spot connect WS error, retrying...')
                self.logger.error('Binance spot connect WS error: %s', str(e))
                time.sleep(5)

        ltime = time.time()
        print("Connected to WebSocket.")

        while True:
            try:
                result = ws.recv()
                if 'ping' in result:
                    ws.send(result.replace('ping', 'pong'))
                else:
                    data = json.loads(result)
                    
                    if 'stream' in data and '@depth20' in data['stream']:
                        if 'data' in data:
                            newdata = {
                                'stream': data['stream'].upper(),
                                'data': [{
                                    'bids': data['data']['bids'],
                                    'asks': data['data']['asks'],
                                    'cts': int(1000 * time.time()),  # 当前时间戳（毫秒）
                                    'ts': int(1000 * time.time()),   # 当前时间戳（毫秒）
                                    'instrument_id': data['stream'].split('@')[0].upper()  # 交易对ID
                                }]
                            }
                            # 通过Redis发布市场深度数据
                            self.redis.rpush('b-depth', pickle.dumps(newdata))
                            print(newdata)
                            self.lasttime[self.instrument.upper()] = time.time()

                    # 每60秒记录一次数据
                    if time.time() - ltime > 60:
                        self.logger.info(data['stream'])
                        ltime = time.time()

                # 检查行情中断
                if time.time() - self.lasttime[self.instrument.upper()] > 20:
                    self.logger.error("Market data interrupted, exiting...")
                    sys.exit(0)

            except Exception as e:
                self.logger.error("Binance spot run -> traceback = %s" % traceback.format_exc())
                break


if __name__ == "__main__":
    instrument = "usdcusdt"  
    market = MarketData(instrument)
    market.market_data()  