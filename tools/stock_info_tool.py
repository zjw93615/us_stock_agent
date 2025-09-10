# 股票基本信息获取工具
from typing import Dict
from tools.base_tool import Tool
from logger import get_logger

# 获取日志记录器
logger = get_logger()

class StockInfoTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_stock_info",
            description="获取股票的基本信息，包括公司简介、行业分类、市值、股价、52周高低点等基础数据",
            parameters={
                "ticker": {"type": "str", "description": "股票代码，如AAPL"}
            },
        )

    def run(self, ticker: str) -> Dict:
        logger.info(f"获取股票基本信息: 股票={ticker}")
        import yfinance as yf

        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 精简数据：提取关键信息
            result = {
                "ticker": ticker,
                "company_info": {
                    "name": info.get("longName", "N/A"),
                    "sector": info.get("sector", "N/A"),
                    "industry": info.get("industry", "N/A"),
                    "country": info.get("country", "N/A"),
                    "website": info.get("website", "N/A"),
                    "business_summary": info.get("longBusinessSummary", "N/A"),
                    "full_time_employees": info.get("fullTimeEmployees", "N/A"),
                },
                "stock_data": {
                    "current_price": info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
                    "previous_close": info.get("previousClose", "N/A"),
                    "open": info.get("open", info.get("regularMarketOpen", "N/A")),
                    "day_low": info.get("dayLow", info.get("regularMarketDayLow", "N/A")),
                    "day_high": info.get("dayHigh", info.get("regularMarketDayHigh", "N/A")),
                    "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
                    "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                    "volume": info.get("volume", info.get("regularMarketVolume", "N/A")),
                    "avg_volume": info.get("averageVolume", "N/A"),
                    "market_cap": info.get("marketCap", "N/A"),
                    "beta": info.get("beta", "N/A"),
                    "price_to_earnings": info.get("trailingPE", "N/A"),
                    "earnings_per_share": info.get("trailingEps", "N/A"),
                    "forward_dividend_yield": info.get("dividendYield", "N/A") if info.get("dividendYield") is not None else "N/A",
                    "ex_dividend_date": info.get("exDividendDate", "N/A"),
                },
                "analysts_data": {
                    "target_price": info.get("targetMeanPrice", "N/A"),
                    "target_high": info.get("targetHighPrice", "N/A"),
                    "target_low": info.get("targetLowPrice", "N/A"),
                    "recommendation": info.get("recommendationKey", "N/A"),
                    "number_of_analysts": info.get("numberOfAnalystOpinions", "N/A"),
                }
            }
            
            logger.info(f"成功获取{ticker}的基本信息")
            return result
        except Exception as e:
            logger.error(f"获取股票基本信息失败: {str(e)}")
            raise