import redis
import pickle

class listen_redis:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis = redis.StrictRedis(host=redis_host, port=redis_port)
        self.pubsub = self.redis.pubsub()

    def subscribe(self, channel):
        self.pubsub.subscribe(channel)
        print(f"Subscribed to channel: {channel}")

    def listen(self):
        #监听消息
        print("Listening for messages...")
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = pickle.loads(message['data'])
                    self.process_data(data)
                except Exception as e:
                    print(f"Error processing message: {e}")

    def process_data(self, data):
        print(f"Received data: {data}")

if __name__ == "__main__":
    subscriber = listen_redis()
    subscriber.subscribe('b-depth')
    subscriber.listen()