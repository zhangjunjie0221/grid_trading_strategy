import unittest
from unittest.mock import MagicMock, call, patch
from strategy.grid_strategy import Strategy


class TestStrategyFunctionality(unittest.TestCase):
    def setUp(self):
        self.mock_api_client = MagicMock()
        self.mock_database = MagicMock()

        #代实际的Database
        with patch('strategy.grid_strategy.Database', return_value=self.mock_database):
            self.strategy = Strategy()
        
        self.strategy.api_client = self.mock_api_client

        #设置初始订单数据
        self.strategy.orders = {
            1.0: 10,
            2.0: 20
        }
        self.strategy.step = 0.1 

    def tearDown(self):
        self.strategy.close()

    def test_create_maker_order_success(self):
        #设置模拟的返回值
        mock_order_id = '12345'
        self.mock_api_client.create_order.return_value = mock_order_id
        
        #执行下单操作
        order_id = self.strategy.create_maker_order('USDCUSDT', 1, 1.0, 'BUY')
        
        #验证返回的订单ID和存储方法是否被调用
        self.assertEqual(order_id, mock_order_id)
        self.mock_database.store_order_id.assert_called_once_with(mock_order_id)


    def test_create_maker_order_failure(self):
        #设置模拟的异常
        self.mock_api_client.create_order.side_effect = Exception("API Error")
        
        #执行下单操作
        order_id = self.strategy.create_maker_order('USDCUSDT', 1, 1.0, 'BUY')

        #验证返回值应为None
        self.assertIsNone(order_id)
        self.mock_database.store_order_id.assert_not_called()

    def test_check_order_status_success(self):
        # 设置模拟的返回值
        order_id = '12345'
        self.mock_api_client.get_order_status.return_value = {
            'status': 'FILLED',
            'filled_amount': 1,
            'average_fill_price': 1.0,
            'order_type': 'BUY',
            'remaining_amount': 0
        }
        
        # 执行检查订单状态操作
        status = self.strategy.check_order_status(order_id)
        
        # 验证返回的状态信息
        self.assertEqual(status['status'], 'FILLED')

    def test_check_order_status_failure(self):
        # 设置模拟的异常
        order_id = '12345'
        self.mock_api_client.get_order_status.side_effect = Exception("API Error")
        
        #执行检查订单状态操作
        status = self.strategy.check_order_status(order_id)
        
        #验证返回值应为 {}
        self.assertEqual(status, {})


    def test_first_create_orders(self):
        #设置模拟的返回值
        mock_order_id = '12345'
        self.mock_api_client.create_order.return_value = mock_order_id
        
        #执行初始化订单
        self.strategy.first_create_orders()
        
        #验证create_order被正确调用
        self.assertEqual(self.mock_api_client.create_order.call_count, 2)  #预期调用次数 因为有两个订单
        
        #验证存储订单ID的次数
        self.assertEqual(self.mock_database.store_order_id.call_count, 2)

        calls = self.mock_api_client.create_order.call_args_list

        self.assertIn(call(self.strategy.pairs, 'BUY', 1.0, 10.0), calls)
        self.assertIn(call(self.strategy.pairs, 'BUY', 2.0, 10.0), calls)

if __name__ == '__main__':
    unittest.main()