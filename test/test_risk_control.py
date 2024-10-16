import unittest 
from strategy.risk_control import RiskControl  

class TestRiskControl(unittest.TestCase):
    def setUp(self):
        self.risk_control = RiskControl()

    def test_get_total_asset(self):
        #测试获取总资产的功能
        total_asset = self.risk_control.get_total_asset()
        print(f"当前总资产: {total_asset}")

    def test_monitor_assets(self):
        #测试实时监控资产的功能
        try:
            self.risk_control.min_asset = 1000  
            self.risk_control.monitor_assets()
            print("资产监控功能正常")
        except Exception as e:
            self.fail(f"监控资产时发生错误: {e}")

    def test_cancel_all_orders(self):
        #测试取消所有未成交订单的功能
        try:
            self.risk_control.cancel_all_orders()
            print("未成交订单取消功能正常")
        except Exception as e:
            self.fail(f"取消未成交订单时发生错误: {e}")

if __name__ == "__main__":
    unittest.main()