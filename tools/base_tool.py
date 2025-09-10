# 工具基类
from pydantic import BaseModel, Field
from typing import Dict, Any
from logger import get_logger
# 获取日志记录器
logger = get_logger()

class Tool(BaseModel):
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具功能描述")
    parameters: Dict[str, Any] = Field(..., description="工具参数说明")

    def run(self, **kwargs) -> Any:
        """执行工具"""
        logger.debug(f"工具基类run方法被调用，参数: {kwargs}")
        raise NotImplementedError("子类必须实现run方法")