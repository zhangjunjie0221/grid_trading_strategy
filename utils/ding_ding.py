import base64
import requests
import json
import time
import hmac
import hashlib
from urllib.parse import quote, quote_plus
from config.config import webhook_url, secret
from config.logger import setup_logger

class DingDing:
    def __init__(self):
        self.webhook_url = webhook_url
        self.secret = secret
        self.logger = setup_logger('dingding', 'dingding.log')

    def sign(self):
        '''计算签名'''
        timestamp = str(round(time.time() * 1000))  # 当前时间戳
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f"{timestamp}\n{self.secret}"
        string_to_sign_enc = string_to_sign.encode('utf-8')
        
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = quote_plus(base64.b64encode(hmac_code).decode('utf-8'))  # URL 编码签名
        
        return timestamp, sign

    def send_alert(self, message):
        '''发送钉钉报警消息'''
        timestamp, sign = self.sign()  # 调用 sign 方法，获取时间戳和签名

        # 构造完整的请求 URL
        url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"

        headers = {'Content-Type': 'application/json'}
        data = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                self.logger.debug(f"钉钉消息发送成功,{message}")
            else:
                self.logger.debug(f"钉钉消息发送失败，状态码: {response.status_code}, 错误信息: {response.text}")
        except Exception as e:
            self.logger.debug(f"发送钉钉消息时发生错误: {e}")

