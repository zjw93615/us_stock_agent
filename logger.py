import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# 全局变量存储单例logger
_logger_instance = None
_log_filename = None
_log_level_str = None

def _initialize_logger():
    """初始化日志记录器（单例模式）"""
    global _logger_instance, _log_filename, _log_level_str
    
    if _logger_instance is not None:
        return _logger_instance
    
    # 加载环境变量
    load_dotenv()
    
    # 创建logs目录（如果不存在）
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # 检查是否是Flask调试模式的重启进程
    import sys
    is_reloader = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    
    # 如果是重启进程，尝试复用已存在的日志文件
    if is_reloader:
        # 查找最近创建的日志文件（最近30秒内）
        import glob
        import time
        current_time = datetime.now()
        pattern = os.path.join(log_dir, f'stock_agent_{current_time.strftime("%Y%m%d_%H%M")}*.log')
        existing_files = glob.glob(pattern)
        
        # 过滤出30秒内创建的文件
        recent_files = []
        current_timestamp = time.time()
        for file_path in existing_files:
            file_timestamp = os.path.getctime(file_path)
            if current_timestamp - file_timestamp <= 30:  # 30秒内
                recent_files.append(file_path)
        
        if recent_files:
            # 使用最新的日志文件
            _log_filename = max(recent_files, key=os.path.getctime)
        else:
            # 生成新的日志文件名
            _log_filename = os.path.join(
                log_dir, f'stock_agent_{current_time.strftime("%Y%m%d_%H%M%S")}.log'
            )
    else:
        # 主进程，生成新的日志文件名
        _log_filename = os.path.join(
            log_dir, f'stock_agent_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
    
    # 从环境变量读取日志级别配置
    _log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = log_level_map.get(_log_level_str, logging.INFO)
    
    # 配置日志记录器
    _logger_instance = logging.getLogger("stock_agent")
    
    # 检查是否已经配置过处理器，避免重复添加
    if not _logger_instance.handlers:
        _logger_instance.setLevel(log_level)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(_log_filename, encoding="utf-8")
        file_handler.setLevel(log_level)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # 创建格式化器 - 确保完整输出日志内容，不进行任何省略
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器到记录器
        _logger_instance.addHandler(file_handler)
        _logger_instance.addHandler(console_handler)
        
        # 记录日志配置信息
        process_type = "重启进程" if is_reloader else "主进程"
        _logger_instance.info(f"日志配置 ({process_type}): 级别={_log_level_str}, 文件={_log_filename}")
    
    return _logger_instance

def get_logger():
    """获取日志记录器"""
    return _initialize_logger()
