import threading
from strategy.risk_control import RiskControl
from strategy.grid_strategy import Strategy

def run_risk_control():
    risk_control = RiskControl()
    risk_control.monitor_assets()  # 启动资产监控

def run_strategy():
    strategy = Strategy()
    strategy.Logical_trading()  # 启动逻辑交易

if __name__ == "__main__":
    #创建并启动风控线程
    risk_control_thread = threading.Thread(target=run_risk_control)
    risk_control_thread.start()

    #启动策略
    run_strategy()

    #启动风控
    risk_control_thread.join()