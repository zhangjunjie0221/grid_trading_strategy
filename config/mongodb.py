from pymongo import MongoClient
from config.config import MONGO_CONFIG

class Database:
    def __init__(self):
        # MongoDB 连接
        self.mongo_client = MongoClient(MONGO_CONFIG['uri'])
        self.mongo_db = self.mongo_client[MONGO_CONFIG['db_name']]
        self.collection = self.mongo_db[MONGO_CONFIG['collection_name']]

    def store_order_id(self, order_id):
        self.collection.insert_one({'order_id': order_id})

    def remove_order_id(self, order_id):
        self.collection.delete_one({'order_id': order_id})

    def get_all_order_ids(self):
        return [doc['order_id'] for doc in self.collection.find()]
