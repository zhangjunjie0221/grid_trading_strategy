import logging
import os

def setup_logger(name, log_file):
    # 创建 log 文件夹如果它不存在
    if not os.path.exists('log'):
        os.makedirs('log')
    
    log_file_path = os.path.join('log', log_file)  # 将文件放在 log 文件夹中
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 检查是否已经有handler避免重复添加
    if not logger.hasHandlers():
        handler = logging.FileHandler(log_file_path, mode='a')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger