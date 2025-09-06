import logging
import os
from datetime import datetime

# 创建logs目录（如果不存在）
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 生成日志文件名，包含日期时间
log_filename = os.path.join(log_dir, f'stock_agent_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# 配置日志记录器
logger = logging.getLogger('stock_agent')
logger.setLevel(logging.DEBUG)

# 创建文件处理器
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建格式化器 - 确保完整输出日志内容，不进行任何省略
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 禁用日志记录器的省略功能
logging.getLogger().handlers = []

# 添加处理器到记录器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def get_logger():
    """获取日志记录器"""
    return logger