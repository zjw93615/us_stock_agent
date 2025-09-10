# 技术指标分析工具
from tool_manager import DETAIL_PERIOD
from tools.base_tool import Tool
from typing import Dict
from logger import get_logger

# 获取日志记录器
logger = get_logger()

class TechnicalAnalysisTool(Tool):
    def __init__(self):
        super().__init__(
            name="calculate_technical_indicators",
            description="计算股票的技术指标，包括移动平均线、RSI、MACD、布林带、KDJ等常用指标",
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
        logger.info(
            f"计算技术指标: 股票={ticker}, 开始日期={start_date}, 结束日期={end_date}"
        )
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
                "calculation_date": df.index[-1].strftime("%Y-%m-%d"),
                "data_period": f"使用了{len(df)}天的数据",
                "current_price": float(df["Close"].iloc[-1]),
                "latest_indicators": {},
                "recent_indicators": {},
            }

            # 移动平均线
            sma5 = talib.SMA(df["Close"], timeperiod=5)
            sma10 = talib.SMA(df["Close"], timeperiod=10)
            sma20 = talib.SMA(df["Close"], timeperiod=20)
            sma50 = talib.SMA(df["Close"], timeperiod=50)
            sma100 = talib.SMA(df["Close"], timeperiod=100)

            result["latest_indicators"]["moving_averages"] = {
                "SMA5": float(sma5.iloc[-1]) if not pd.isna(sma5.iloc[-1]) else None,
                "SMA10": float(sma10.iloc[-1]) if not pd.isna(sma10.iloc[-1]) else None,
                "SMA20": float(sma20.iloc[-1]) if not pd.isna(sma20.iloc[-1]) else None,
                "SMA50": float(sma50.iloc[-1]) if not pd.isna(sma50.iloc[-1]) else None,
                "SMA100": (
                    float(sma100.iloc[-1]) if not pd.isna(sma100.iloc[-1]) else None
                ),
            }

            result["recent_indicators"]["date"] = [
                date.strftime("%Y-%m-%d") for date in df.index[-DETAIL_PERIOD:]
            ]
            # 最近10天的移动平均线
            result["recent_indicators"]["sma5"] = [
                float(x) for x in sma5.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]
            result["recent_indicators"]["sma10"] = [
                float(x) for x in sma10.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]
            result["recent_indicators"]["sma20"] = [
                float(x) for x in sma20.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]
            result["recent_indicators"]["sma50"] = [
                float(x) for x in sma50.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]
            result["recent_indicators"]["sma100"] = [
                float(x) for x in sma100.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]

            # RSI
            rsi = talib.RSI(df["Close"], timeperiod=14)
            result["latest_indicators"]["RSI"] = (
                float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
            )
            result["recent_indicators"]["rsi"] = [
                float(x) for x in rsi.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]

            # MACD
            macd, macd_signal, macd_hist = talib.MACD(df["Close"])
            result["latest_indicators"]["MACD"] = {
                "MACD": float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None,
                "Signal": (
                    float(macd_signal.iloc[-1])
                    if not pd.isna(macd_signal.iloc[-1])
                    else None
                ),
                "Histogram": (
                    float(macd_hist.iloc[-1])
                    if not pd.isna(macd_hist.iloc[-1])
                    else None
                ),
            }
            result["recent_indicators"]["macd"] = [
                float(x) for x in macd.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]
            result["recent_indicators"]["macd_signal"] = [
                float(x) for x in macd_signal.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]

            # 布林带
            bb_upper, bb_middle, bb_lower = talib.BBANDS(df["Close"], timeperiod=20)
            result["latest_indicators"]["Bollinger_Bands"] = {
                "Upper": (
                    float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None
                ),
                "Middle": (
                    float(bb_middle.iloc[-1])
                    if not pd.isna(bb_middle.iloc[-1])
                    else None
                ),
                "Lower": (
                    float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None
                ),
            }
            result["recent_indicators"]["bb_upper"] = [
                float(x) for x in bb_upper.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]
            result["recent_indicators"]["bb_lower"] = [
                float(x) for x in bb_lower.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]

            # KDJ指标
            slowk, slowd = talib.STOCH(df["High"], df["Low"], df["Close"])
            result["latest_indicators"]["KDJ"] = {
                "K": float(slowk.iloc[-1]) if not pd.isna(slowk.iloc[-1]) else None,
                "D": float(slowd.iloc[-1]) if not pd.isna(slowd.iloc[-1]) else None,
                "J": (
                    float(3 * slowk.iloc[-1] - 2 * slowd.iloc[-1])
                    if not pd.isna(slowk.iloc[-1]) and not pd.isna(slowd.iloc[-1])
                    else None
                ),
            }
            result["recent_indicators"]["kdj_k"] = [
                float(x) for x in slowk.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]
            result["recent_indicators"]["kdj_d"] = [
                float(x) for x in slowd.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]

            # 威廉指标
            willr = talib.WILLR(df["High"], df["Low"], df["Close"], timeperiod=14)
            result["latest_indicators"]["Williams_R"] = (
                float(willr.iloc[-1]) if not pd.isna(willr.iloc[-1]) else None
            )
            result["recent_indicators"]["williams_r"] = [
                float(x) for x in willr.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]

            # CCI指标
            cci = talib.CCI(df["High"], df["Low"], df["Close"], timeperiod=14)
            result["latest_indicators"]["CCI"] = (
                float(cci.iloc[-1]) if not pd.isna(cci.iloc[-1]) else None
            )
            result["recent_indicators"]["cci"] = [
                float(x) for x in cci.tail(DETAIL_PERIOD) if not pd.isna(x)
            ]

            # 成交量指标
            result["latest_indicators"]["volume"] = {
                "current_volume": int(df["Volume"].iloc[-1]),
                "avg_volume_20": float(df["Volume"].tail(20).mean()),
                "volume_ratio": float(
                    df["Volume"].iloc[-1] / df["Volume"].tail(20).mean()
                ),
            }

            # 价格趋势分析
            result["latest_indicators"]["trend_analysis"] = {
                "price_above_sma20": (
                    float(df["Close"].iloc[-1]) > float(sma20.iloc[-1])
                    if not pd.isna(sma20.iloc[-1])
                    else None
                ),
                "price_above_sma50": (
                    float(df["Close"].iloc[-1]) > float(sma50.iloc[-1])
                    if not pd.isna(sma50.iloc[-1])
                    else None
                ),
                "sma20_above_sma50": (
                    float(sma20.iloc[-1]) > float(sma50.iloc[-1])
                    if not pd.isna(sma20.iloc[-1]) and not pd.isna(sma50.iloc[-1])
                    else None
                ),
            }

            logger.info(
                f"成功计算{ticker}的技术指标，返回最新指标值和最近{DETAIL_PERIOD}个交易日数据"
            )
            return result
        except Exception as e:
            logger.error(f"计算技术指标失败: {str(e)}")
            raise
