# 历史数据获取工具
from typing import Dict
from logger import get_logger
from tool_manager import DETAIL_PERIOD
from .base_tool import Tool

# 获取日志记录器
logger = get_logger()

class HistoricalDataTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_historical_data",
            description="获取股票历史价格数据，包括开盘价、收盘价、最高价、最低价和成交量",
            parameters={
                "ticker": {"type": "str", "description": "股票代码，如AAPL"},
                "start_date": {
                    "type": "str",
                    "description": "开始日期，格式YYYY-MM-DD",
                },
                "end_date": {"type": "str", "description": "结束日期，格式YYYY-MM-DD"},
            },
        )

    def run(self, ticker: str, start_date: str, end_date: str) -> Dict:
        # 实际实现中调用之前的StockDataFetcher
        logger.info(
            f"获取历史数据: 股票={ticker}, 开始日期={start_date}, 结束日期={end_date}"
        )
        import yfinance as yf

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
                    "start_date": start_date or hist.index[0].strftime("%Y-%m-%d"),
                    "end_date": end_date or hist.index[-1].strftime("%Y-%m-%d"),
                    "total_days": len(hist),
                    "current_price": float(hist["Close"].iloc[-1]),
                    "period_high": float(hist["High"].max()),
                    "period_low": float(hist["Low"].min()),
                    "period_return": float(
                        (hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100
                    ),
                    "avg_volume": float(hist["Volume"].mean()),
                    "volatility": float(hist["Close"].pct_change().std() * 100),
                },
                "recent_data": [],
            }

            # 最近的详细数据
            recent_hist = (
                hist.tail(DETAIL_PERIOD) if len(hist) > DETAIL_PERIOD else hist
            )
            for date, row in recent_hist.iterrows():
                summary["recent_data"].append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"]),
                    }
                )

            logger.info(f"已精简{ticker}的历史数据，减少token消耗")
            return summary
        except Exception as e:
            logger.error(f"获取历史数据失败: {str(e)}")
            raise