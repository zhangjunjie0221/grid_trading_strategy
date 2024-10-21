from clients.binance_api import Binance
from config.config import API_KEY, API_SECRET


def main():
    binance = Binance(API_KEY, API_SECRET)
    try:
        account_info = binance.get_account()
        print("账户信息:", account_info)
    except Exception as e:
        print("获取账户信息失败:", e , account_info)


    # #测试创建订单
    # try:
    #     order_id = binance.create_order(symbol='USDCUSDT', side='BUY', quantity=6, price=0.9999)
    #     print("创建订单成功，订单 ID:", order_id)
    # except Exception as e:
    #     print("创建订单失败:", e)

    # #测试获取订单状态
    # try:
    #     status = binance.get_order_status(symbol='USDCUSDT', order_id=659686676)
    #     print("订单状态:", status)
    # except Exception as e:
    #     print("获取订单状态失败:", e,status)

    # # 测试取消订单
    # try:
    #     cancellation_result = binance.cancel_order(symbol='USDCUSDT', order_id=659686676)
    #     print("取消订单结果:", cancellation_result)
    # except Exception as e:
    #     print("取消订单失败:", e)

    
   
    # # 测试获取未成交订单
    # try:
    #     open_orders = binance.get_open_orders(symbol='USDCUSDT')
    #     print("未成交订单:", open_orders)
    # except Exception as e:
    #     print("获取未成交订单失败:", e)

if __name__ == "__main__":
    main()