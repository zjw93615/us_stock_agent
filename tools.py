from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from logger import get_logger

DETAIL_PERIOD = 5

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
        import pandas as pd
        stock = yf.Ticker(ticker)
        try:
            hist = stock.history(start=start_date, end=end_date)
            logger.info(f"成功获取{ticker}的历史数据，记录数: {len(hist)}")
            
            # 精简数据：只返回关键统计信息和最近几天的数据
            if len(hist) == 0:
                return {"error": "未获取到数据"}
            
            # 计算关键统计信息
            summary = {
                "ticker": ticker,
                "period_summary": {
                    "start_date": start_date or hist.index[0].strftime('%Y-%m-%d'),
                    "end_date": end_date or hist.index[-1].strftime('%Y-%m-%d'),
                    "total_days": len(hist),
                    "current_price": float(hist['Close'].iloc[-1]),
                    "period_high": float(hist['High'].max()),
                    "period_low": float(hist['Low'].min()),
                    "period_return": float((hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100),
                    "avg_volume": float(hist['Volume'].mean()),
                    "volatility": float(hist['Close'].pct_change().std() * 100)
                },
                "recent_data": [],
            }
            
            # 最近的详细数据
            recent_hist = hist.tail(DETAIL_PERIOD) if len(hist) > DETAIL_PERIOD else hist
            for date, row in recent_hist.iterrows():
                summary["recent_data"].append({
                    "date": date.strftime('%Y-%m-%d'),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume'])
                })
            
            
            logger.info(f"已精简{ticker}的历史数据，减少token消耗")
            return summary
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
        import pandas as pd
        stock = yf.Ticker(ticker)
        try:
            # 获取原始财务数据
            balance_sheet = stock.balance_sheet
            income_stmt = stock.income_stmt
            cash_flow = stock.cashflow
            info = stock.info
            
            # 精简财务数据：只提取关键指标
            result = {
                "key_metrics": {
                    # 基本信息
                    "market_cap": info.get('marketCap', 'N/A'),
                    "pe_ratio": info.get('trailingPE', 'N/A'),
                    "pb_ratio": info.get('priceToBook', 'N/A'),
                    "dividend_yield": info.get('dividendYield', 'N/A'),
                    "debt_to_equity": info.get('debtToEquity', 'N/A'),
                    "roe": info.get('returnOnEquity', 'N/A'),
                    "profit_margin": info.get('profitMargins', 'N/A')
                },
                "recent_financials": {}
            }
            
            # 从财务报表中提取关键数据（最近一期）
            if not income_stmt.empty:
                latest_income = income_stmt.iloc[:, 0]  # 最新一期数据
                result["recent_financials"].update({
                    "total_revenue": float(latest_income.get('Total Revenue', 0)) if pd.notna(latest_income.get('Total Revenue', 0)) else 0,
                    "net_income": float(latest_income.get('Net Income', 0)) if pd.notna(latest_income.get('Net Income', 0)) else 0,
                    "gross_profit": float(latest_income.get('Gross Profit', 0)) if pd.notna(latest_income.get('Gross Profit', 0)) else 0
                })
            
            if not balance_sheet.empty:
                latest_balance = balance_sheet.iloc[:, 0]  # 最新一期数据
                result["recent_financials"].update({
                    "total_assets": float(latest_balance.get('Total Assets', 0)) if pd.notna(latest_balance.get('Total Assets', 0)) else 0,
                    "total_debt": float(latest_balance.get('Total Debt', 0)) if pd.notna(latest_balance.get('Total Debt', 0)) else 0,
                    "shareholders_equity": float(latest_balance.get('Stockholders Equity', 0)) if pd.notna(latest_balance.get('Stockholders Equity', 0)) else 0
                })
            
            if not cash_flow.empty:
                latest_cashflow = cash_flow.iloc[:, 0]  # 最新一期数据
                result["recent_financials"].update({
                    "operating_cash_flow": float(latest_cashflow.get('Operating Cash Flow', 0)) if pd.notna(latest_cashflow.get('Operating Cash Flow', 0)) else 0,
                    "free_cash_flow": float(latest_cashflow.get('Free Cash Flow', 0)) if pd.notna(latest_cashflow.get('Free Cash Flow', 0)) else 0
                })
            
            logger.info(f"成功获取并精简{ticker}的财务数据，减少token消耗")
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
            description="计算股票的技术指标，包括移动平均线、RSI、MACD、布林带、KDJ等常用指标",
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
        import numpy as np
        
        try:
            stock = yf.Ticker(ticker)
            
            # 根据参数选择获取数据的方式
            df = stock.history(start=start_date, end=end_date)
            
            if len(df) < 100:
                logger.info(f"查询日期少于100个交易日，使用100天数据进行计算")
                df = stock.history(period="100d")
            
            logger.debug(f"成功获取{ticker}的历史数据，记录数: {len(df)}")
            
            # 返回最新的指标值和最近10个交易日数据
            result = {
                "ticker": ticker,
                "calculation_date": df.index[-1].strftime('%Y-%m-%d'),
                "data_period": f"使用了{len(df)}天的数据",
                "current_price": float(df['Close'].iloc[-1]),
                "latest_indicators": {},
                "recent_indicators": {}
            }
            
            # 移动平均线
            sma5 = talib.SMA(df['Close'], timeperiod=5)
            sma10 = talib.SMA(df['Close'], timeperiod=10)
            sma20 = talib.SMA(df['Close'], timeperiod=20)
            sma50 = talib.SMA(df['Close'], timeperiod=50)
            sma100 = talib.SMA(df['Close'], timeperiod=100)
            
            result['latest_indicators']['moving_averages'] = {
                "SMA5": float(sma5.iloc[-1]) if not pd.isna(sma5.iloc[-1]) else None,
                "SMA10": float(sma10.iloc[-1]) if not pd.isna(sma10.iloc[-1]) else None,
                "SMA20": float(sma20.iloc[-1]) if not pd.isna(sma20.iloc[-1]) else None,
                "SMA50": float(sma50.iloc[-1]) if not pd.isna(sma50.iloc[-1]) else None,
                "SMA100": float(sma100.iloc[-1]) if not pd.isna(sma100.iloc[-1]) else None
            }
            
            result['recent_indicators']['date'] = [date.strftime('%Y-%m-%d') for date in df.index[-DETAIL_PERIOD:]]
            # 最近10天的移动平均线
            result['recent_indicators']['sma5'] = [float(x) for x in sma5.tail(DETAIL_PERIOD) if not pd.isna(x)]
            result['recent_indicators']['sma10'] = [float(x) for x in sma10.tail(DETAIL_PERIOD) if not pd.isna(x)]
            result['recent_indicators']['sma20'] = [float(x) for x in sma20.tail(DETAIL_PERIOD) if not pd.isna(x)]
            result['recent_indicators']['sma50'] = [float(x) for x in sma50.tail(DETAIL_PERIOD) if not pd.isna(x)]
            result['recent_indicators']['sma100'] = [float(x) for x in sma100.tail(DETAIL_PERIOD) if not pd.isna(x)]
            
            # RSI
            rsi = talib.RSI(df['Close'], timeperiod=14)
            result['latest_indicators']['RSI'] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
            result['recent_indicators']['rsi'] = [float(x) for x in rsi.tail(DETAIL_PERIOD) if not pd.isna(x)]
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(df['Close'])
            result['latest_indicators']['MACD'] = {
                "MACD": float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None,
                "Signal": float(macd_signal.iloc[-1]) if not pd.isna(macd_signal.iloc[-1]) else None,
                "Histogram": float(macd_hist.iloc[-1]) if not pd.isna(macd_hist.iloc[-1]) else None
            }
            result['recent_indicators']['macd'] = [float(x) for x in macd.tail(DETAIL_PERIOD) if not pd.isna(x)]
            result['recent_indicators']['macd_signal'] = [float(x) for x in macd_signal.tail(DETAIL_PERIOD) if not pd.isna(x)]
            
            # 布林带
            bb_upper, bb_middle, bb_lower = talib.BBANDS(df['Close'], timeperiod=20)
            result['latest_indicators']['Bollinger_Bands'] = {
                "Upper": float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None,
                "Middle": float(bb_middle.iloc[-1]) if not pd.isna(bb_middle.iloc[-1]) else None,
                "Lower": float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None
            }
            result['recent_indicators']['bb_upper'] = [float(x) for x in bb_upper.tail(DETAIL_PERIOD) if not pd.isna(x)]
            result['recent_indicators']['bb_lower'] = [float(x) for x in bb_lower.tail(DETAIL_PERIOD) if not pd.isna(x)]
            
            # KDJ指标
            slowk, slowd = talib.STOCH(df['High'], df['Low'], df['Close'])
            result['latest_indicators']['KDJ'] = {
                "K": float(slowk.iloc[-1]) if not pd.isna(slowk.iloc[-1]) else None,
                "D": float(slowd.iloc[-1]) if not pd.isna(slowd.iloc[-1]) else None,
                "J": float(3 * slowk.iloc[-1] - 2 * slowd.iloc[-1]) if not pd.isna(slowk.iloc[-1]) and not pd.isna(slowd.iloc[-1]) else None
            }
            result['recent_indicators']['kdj_k'] = [float(x) for x in slowk.tail(DETAIL_PERIOD) if not pd.isna(x)]
            result['recent_indicators']['kdj_d'] = [float(x) for x in slowd.tail(DETAIL_PERIOD) if not pd.isna(x)]
            
            # 威廉指标
            willr = talib.WILLR(df['High'], df['Low'], df['Close'], timeperiod=14)
            result['latest_indicators']['Williams_R'] = float(willr.iloc[-1]) if not pd.isna(willr.iloc[-1]) else None
            result['recent_indicators']['williams_r'] = [float(x) for x in willr.tail(DETAIL_PERIOD) if not pd.isna(x)]
            
            # CCI指标
            cci = talib.CCI(df['High'], df['Low'], df['Close'], timeperiod=14)
            result['latest_indicators']['CCI'] = float(cci.iloc[-1]) if not pd.isna(cci.iloc[-1]) else None
            result['recent_indicators']['cci'] = [float(x) for x in cci.tail(DETAIL_PERIOD) if not pd.isna(x)]
            
            # 成交量指标
            result['latest_indicators']['volume'] = {
                "current_volume": int(df['Volume'].iloc[-1]),
                "avg_volume_20": float(df['Volume'].tail(20).mean()),
                "volume_ratio": float(df['Volume'].iloc[-1] / df['Volume'].tail(20).mean())
            }
            
            # 价格趋势分析
            result['latest_indicators']['trend_analysis'] = {
                "price_above_sma20": float(df['Close'].iloc[-1]) > float(sma20.iloc[-1]) if not pd.isna(sma20.iloc[-1]) else None,
                "price_above_sma50": float(df['Close'].iloc[-1]) > float(sma50.iloc[-1]) if not pd.isna(sma50.iloc[-1]) else None,
                "sma20_above_sma50": float(sma20.iloc[-1]) > float(sma50.iloc[-1]) if not pd.isna(sma20.iloc[-1]) and not pd.isna(sma50.iloc[-1]) else None
            }
            
            logger.info(f"成功计算{ticker}的技术指标，返回最新指标值和最近{DETAIL_PERIOD}个交易日数据")
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
