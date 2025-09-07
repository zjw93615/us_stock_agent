from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from logger import get_logger

# 获取日志记录器
logger = get_logger()

# 工具基类
class Tool(BaseModel):
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具功能描述")
    parameters: Dict[str, Any] = Field(..., description="工具参数说明")
    
    def run(self, **kwargs) -> Any:
        """执行工具"""
        logger.debug(f"工具基类run方法被调用，参数: {kwargs}")
        raise NotImplementedError("子类必须实现run方法")

# 历史数据获取工具
class HistoricalDataTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_historical_data",
            description="获取股票历史价格数据，包括开盘价、收盘价、最高价、最低价和成交量",
            parameters={
                "ticker": {"type": "str", "description": "股票代码，如AAPL"},
                "start_date": {"type": "str", "description": "开始日期，格式YYYY-MM-DD"},
                "end_date": {"type": "str", "description": "结束日期，格式YYYY-MM-DD"}
            }
        )
    
    def run(self, ticker: str, start_date: str, end_date: str) -> Dict:
        # 实际实现中调用之前的StockDataFetcher
        logger.info(f"获取历史数据: 股票={ticker}, 开始日期={start_date}, 结束日期={end_date}")
        import yfinance as yf
        stock = yf.Ticker(ticker)
        try:
            hist = stock.history(start=start_date, end=end_date)
            logger.info(f"成功获取{ticker}的历史数据，记录数: {len(hist)}")
            return hist.to_dict()
        except Exception as e:
            logger.error(f"获取历史数据失败: {str(e)}")
            raise

# 财务报表获取工具
class FinancialStatementsTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_financial_statements",
            description="获取公司财务报表，包括资产负债表、利润表和现金流量表",
            parameters={
                "ticker": {"type": "str", "description": "股票代码，如AAPL"}
            }
        )
    
    def run(self, ticker: str) -> Dict:
        # 实际实现中调用之前的StockDataFetcher
        logger.info(f"获取财务报表: 股票={ticker}")
        import yfinance as yf
        stock = yf.Ticker(ticker)
        try:
            result = {
                "balance_sheet": stock.balance_sheet.to_dict(),
                "income_stmt": stock.income_stmt.to_dict(),
                "cash_flow": stock.cashflow.to_dict()
            }
            logger.info(f"成功获取{ticker}的财务报表")
            return result
        except Exception as e:
            logger.error(f"获取财务报表失败: {str(e)}")
            raise

# 新闻获取工具
class NewsTool(Tool):
    def __init__(self, api_key: str = None):
        # GNews不需要API密钥，但保留参数以兼容现有代码
        super().__init__(
            name="get_news",
            description="获取相关的新闻 articles",
            parameters={
                "query": {"type": "str", "description": "搜索关键词，通常是股票相关的消息或是希望查询的新闻内容"},
                "from_date": {"type": "str", "description": "开始日期，格式YYYY-MM-DD"},
                "to_date": {"type": "str", "description": "结束日期，格式YYYY-MM-DD"}
            }
        )
    
    def run(self, query: str, from_date: str, to_date: str) -> List[Dict]:
        logger.info(f"获取新闻: 查询={query}, 开始日期={from_date}, 结束日期={to_date}")
        from gnews import GNews
        
        try:
            # 创建GNews实例
            google_news = GNews()
            logger.debug("成功创建GNews实例")
            
            # 设置语言和国家/地区
            google_news.language = 'en'
            google_news.country = 'US'  # 美国新闻源
            google_news.period = '7d'  # 默认为7天内的新闻
            google_news.max_results = 20  # number of responses across a keyword
            # if(from_date and to_date):
            #     from datetime import datetime
            #     from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
            #     to_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
            #     google_news.start_date = (from_date_obj.year, from_date_obj.month, from_date_obj.day)
            #     google_news.end_date = (to_date_obj.year, to_date_obj.month, to_date_obj.day)
            # else:
            #     google_news.period = '7d'  # 默认为7天内的新闻
            logger.debug(f"GNews配置: 语言={google_news.language}, 国家={google_news.country}, 时间段={google_news.period}")
            
            # 获取新闻
            logger.info(f"开始获取关于 '{query}' 的新闻")
            news_results = google_news.get_news(query)
            logger.info(f"成功获取新闻，数量: {len(news_results)}")
            
            # 转换结果格式以匹配原来的API返回格式
            articles = []
            for item in news_results:
                article = {
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'url': item.get('url', ''),
                    'publishedAt': item.get('published date', ''),
                    'source': {
                        'name': item.get('publisher', {}).get('title', '')
                    }
                }
                articles.append(article)
                # 记录每篇文章的详细信息
                logger.debug(f"文章信息: {article}")
            
            logger.debug(f"新闻格式转换完成，返回{len(articles)}条新闻")
            return articles
        except Exception as e:
            logger.error(f"获取新闻失败: {str(e)}")
            raise

# 技术指标分析工具
class TechnicalAnalysisTool(Tool):
    def __init__(self):
        super().__init__(
            name="calculate_technical_indicators",
            description="计算股票的技术指标，如移动平均线、RSI、MACD等",
            parameters={
                "ticker": {"type": "str", "description": "股票代码，如AAPL"},
                "start_date": {"type": "str", "description": "开始日期，格式YYYY-MM-DD"},
                "end_date": {"type": "str", "description": "结束日期，格式YYYY-MM-DD"}
            }
        )
    
    def run(self, ticker: str, start_date: str, end_date: str) -> Dict:
        logger.info(f"计算技术指标: 股票={ticker}, 开始日期={start_date}, 结束日期={end_date}")
        import yfinance as yf
        import talib
        import pandas as pd
        
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
            logger.debug(f"成功获取{ticker}的历史数据，记录数: {len(df)}")
            
            result = {}
            # 计算技术指标
            logger.debug("开始计算技术指标: SMA50, SMA200, RSI, MACD")
            result['SMA50'] = pd.Series(talib.SMA(df['Close'], timeperiod=50)).to_dict()
            result['SMA200'] = pd.Series(talib.SMA(df['Close'], timeperiod=200)).to_dict()
            result['RSI'] = pd.Series(talib.RSI(df['Close'], timeperiod=14)).to_dict()
            
            macd, macd_signal, macd_hist = talib.MACD(df['Close'])
            result['MACD'] = pd.Series(macd).to_dict()
            result['MACD_signal'] = pd.Series(macd_signal).to_dict()
            
            logger.info(f"成功计算{ticker}的技术指标")
            return result
        except Exception as e:
            logger.error(f"计算技术指标失败: {str(e)}")
            raise

# 工具管理器
class ToolManager:
    def __init__(self, news_api_key: str):
        logger.info("初始化工具管理器")
        self.tools = {
            "get_historical_data": HistoricalDataTool(),
            "get_financial_statements": FinancialStatementsTool(),
            "get_news": NewsTool(news_api_key),
            "calculate_technical_indicators": TechnicalAnalysisTool()
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
