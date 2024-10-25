import threading
from strategy.risk_control import RiskControl
from strategy.grid_strategy import Strategy
from websockets.ws import MarketData

def run_risk_control():
    risk_control = RiskControl()
    risk_control.monitor_assets()  # 启动资产监控

def run_strategy():
    strategy = Strategy()
    strategy.Logical_trading()  # 启动逻辑交易

def run_market_data(instrument):
    market = MarketData(instrument)
    market.market_data()  # 启动市场数据获取

if __name__ == "__main__":
    #创建并启动风控线程
    risk_control_thread = threading.Thread(target=run_risk_control)
    risk_control_thread.start()


    #创建并启动策略线程
    strategy_thread = threading.Thread(target=run_strategy)
    strategy_thread.start()


    # 创建并启动市场数据线程
    instrument = "usdcusdt"
    market_data_thread = threading.Thread(target=run_market_data, args=(instrument,))
    market_data_thread.start()

    #启动风控
    risk_control_thread.join()

    strategy_thread.join()
   
    market_data_thread.join()