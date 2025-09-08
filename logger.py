import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建logs目录（如果不存在）
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

# 生成日志文件名，包含日期时间
log_filename = os.path.join(
    log_dir, f'stock_agent_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)

# 从环境变量读取日志级别配置
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
log_level = log_level_map.get(log_level_str, logging.INFO)

# 配置日志记录器
logger = logging.getLogger("stock_agent")
logger.setLevel(log_level)

# 创建文件处理器
file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setLevel(log_level)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)

# 创建格式化器 - 确保完整输出日志内容，不进行任何省略
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 禁用日志记录器的省略功能
logging.getLogger().handlers = []

# 添加处理器到记录器
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def get_logger():
    """获取日志记录器"""
    # 记录日志配置信息
    logger.info(f"日志配置: 级别={log_level_str}, 文件={log_filename}")
    return logger
