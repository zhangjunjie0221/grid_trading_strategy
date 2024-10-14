
from enum import Enum

class TradingPair(Enum):
    USDCUSDT = "USDCUSDT"


# 步长和订单信息
STEP = 0.0001

MIN_ASSET = 1000

ORDERS = {
    1.0002: 80,
    1.0001: 200,
    0.9999: 300,
    0.9998: 200,
    0.9997: 110,
    0.9996: 110
}


# Redis 配置信息
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": ""
}

# MongoDB 配置信息
MONGO_CONFIG = {
    "uri": "mongodb://localhost:27017/",
    "db_name": "trading",
    "collection_name": "orders"
}

# 账户密钥
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"


proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}