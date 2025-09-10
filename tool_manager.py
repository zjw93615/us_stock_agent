from typing import Optional
from logger import get_logger
from tools.base_tool import Tool

DETAIL_PERIOD = 5

# 获取日志记录器
logger = get_logger()

import os
proxy = os.getenv("HTTP_PROXY")
https_proxy = os.getenv("HTTPS_PROXY")
if proxy:
    os.environ['HTTP_PROXY'] = proxy
if https_proxy:
    os.environ['HTTPS_PROXY'] = https_proxy


# 工具管理器
class ToolManager:
    def __init__(self, news_api_key: str):
        from tools.historical_data_tool import HistoricalDataTool
        from tools.financial_statements_tool import FinancialStatementsTool
        from tools.news_tool import NewsTool
        from tools.technical_analysis_tool import TechnicalAnalysisTool
        from tools.stock_info_tool import StockInfoTool
        from tools.web_search_tool import WebSearchIntegrationTool
        logger.info("初始化工具管理器")
        self.tools = {
            "get_historical_data": HistoricalDataTool(),
            "get_financial_statements": FinancialStatementsTool(),
            "get_news": NewsTool(news_api_key),
            "calculate_technical_indicators": TechnicalAnalysisTool(),
            "get_stock_info": StockInfoTool(),
            # "get_historical_pe_eps": HistoricalPEEPSTool(),
            "search_web_info": WebSearchIntegrationTool(),
        }
        logger.info(f"已注册{len(self.tools)}个工具: {', '.join(self.tools.keys())}")

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        tool = self.tools.get(tool_name)
        if tool:
            logger.debug(f"获取工具: {tool_name} - 成功")
        else:
            logger.warning(f"获取工具: {tool_name} - 未找到")
        return tool

    def get_all_tool_descriptions(self) -> str:
        """生成所有工具的描述，用于告知大模型"""
        logger.debug("生成所有工具的描述")
        descriptions = []
        for tool in self.tools.values():
            param_desc = []
            for name, info in tool.parameters.items():
                param_desc.append(f"{name}: {info['type']}, {info['description']}")

            descriptions.append(
                f"- 工具名称: {tool.name}\n"
                f"  描述: {tool.description}\n"
                f"  参数: {', '.join(param_desc)}"
            )

        logger.debug(f"已生成{len(descriptions)}个工具的描述")
        return "\n".join(descriptions)