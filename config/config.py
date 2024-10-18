
from enum import Enum

class TradingPair(Enum):
    USDCUSDT = 'USDCUSDT'


# 步长和订单信息
STEP = 0.0001

MIN_ASSET = 75

# ORDERS = {
#     1.0002: 80,
#     1.0001: 200,
#     0.9999: 300,
#     0.9998: 200,
#     0.9997: 110,
#     0.9996: 110
# }

ORDERS = {
    1.0002: 6,
    1.0001: 16,
    0.9999: 24,
    0.9998: 16,
    0.9997: 8,
    0.9996: 8
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
API_KEY = "t3ImE9ybf6s7tE4QkZ6zwWwdCGAstM9FVn2ucfPOugHizsK29Zqi1QYHov34xcOy"
API_SECRET = "G6ZEkeVQsGjK1WY49ARSbev0kkob4VSRkD2r75zOibPF5mRP2YEMo1VhxiToHbYJ"


proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}

#钉钉配置信息
webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=ae55d8268ce1bff0c03593f292723fc8bfcacc7ad7a0adf33b23d9116957237b"
secret = "SEC539fc1972fd714277a22f56dde3537e15f6168592212fb1c73283618e7b1c95b"