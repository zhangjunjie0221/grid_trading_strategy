import requests

#从官网获取交易对的交易信息
def get_symbol_info(symbol):
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)
    data = response.json()

    for s in data['symbols']:
        if s['symbol'] == symbol:
            return s
    return None

# 替换为你想要查询的交易对，例如 'BTCUSDT'
symbol = 'USDCUSDT'  
symbol_info = get_symbol_info(symbol)

if symbol_info:
    lot_size_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
    if lot_size_filter:
        min_qty = float(lot_size_filter['minQty'])
        max_qty = float(lot_size_filter['maxQty'])
        step_size = float(lot_size_filter['stepSize'])
        print(f"最小交易数量: {min_qty}, 最大交易数量: {max_qty}, 数量步进: {step_size}")