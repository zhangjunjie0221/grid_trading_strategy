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

def test_mongo_connection_and_functions():
    db = Database()
    
    # 测试连接
    try:
        #测试插入
        test_order_id = "test_order_123"
        print("Storing order ID:", test_order_id)
        db.store_order_id(test_order_id)
        
        #测试获取所有订单id
        all_order_ids = db.get_all_order_ids()
        print("All order IDs after insertion:", all_order_ids)

        #测试删除
        print("Removing order ID:", test_order_id)
        db.remove_order_id(test_order_id)


        # 再次获取所有订单 ID
        all_order_ids_after_removal = db.get_all_order_ids()
        print("All order IDs after removal:", all_order_ids_after_removal)

    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    test_mongo_connection_and_functions()