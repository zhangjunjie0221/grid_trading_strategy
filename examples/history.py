from datetime import datetime, timedelta
import requests 
import pandas 


#获取里数据
def data_receve(symbol, interval, start_time_str, end_time_str):
    
    # 使用string_to_timestamp将字符串转换为时间戳
    start_timestamp = string_to_timestamp(start_time_str)
    end_timestamp = string_to_timestamp(end_time_str)
    all_data = []

    while start_timestamp < end_timestamp:
        url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={start_timestamp}&endTime={end_timestamp}'
        response = requests.get(url)
        print(response)
        
        if response.status_code == 200:
            data = response.json()
            if not data:
                break
            all_data.extend(data)
            start_timestamp = data[-1][6] + 1  # 更新 start_timestamp 为最后一条数据的结束时间
        else:
            print("失败", response.status_code)
            break
            
    return all_data

#将数据转化为DataFrame格式
def to_pandas(data_receve):

    data = pandas.DataFrame(
        [[float(i) for i in j[:5]] for j in data_receve],
        columns=["Date", "Open", "High", "Low", "Close"],
    )
    data["Date"] = pandas.to_datetime(data["Date"], unit="ms", utc=True)
    data.set_index("Date", inplace=True)
    data.index = data.index.tz_convert("Asia/Shanghai")
    return data

#将字符串转换为时间戳
def string_to_timestamp(time_string: str) -> int:
    format_string = "%Y-%m-%d %H:%M:%S.%f"
    if " " not in time_string:
        format_string = "%Y-%m-%d"
    elif "." not in time_string:
        format_string = "%Y-%m-%d %H:%M:%S"
    date_time = datetime.strptime(time_string, format_string)
    return int(date_time.timestamp() * 1000)

