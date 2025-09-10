# 财务报表获取工具
from typing import Dict
from tools.base_tool import Tool
from logger import get_logger

# 获取日志记录器
logger = get_logger()

class FinancialStatementsTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_financial_statements",
            description="获取公司财务报表，包括资产负债表、利润表和现金流量表",
            parameters={"ticker": {"type": "str", "description": "股票代码，如AAPL"}},
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
                    "market_cap": info.get("marketCap", "N/A"),
                    "pe_ratio": info.get("trailingPE", "N/A"),
                    "pb_ratio": info.get("priceToBook", "N/A"),
                    "dividend_yield": info.get("dividendYield", "N/A"),
                    "debt_to_equity": info.get("debtToEquity", "N/A"),
                    "roe": info.get("returnOnEquity", "N/A"),
                    "profit_margin": info.get("profitMargins", "N/A"),
                },
                "recent_financials": {},
            }

            # 从财务报表中提取关键数据（最近一期）
            if not income_stmt.empty:
                latest_income = income_stmt.iloc[:, 0]  # 最新一期数据
                result["recent_financials"].update(
                    {
                        "total_revenue": (
                            float(latest_income.get("Total Revenue", 0))
                            if pd.notna(latest_income.get("Total Revenue", 0))
                            else 0
                        ),
                        "net_income": (
                            float(latest_income.get("Net Income", 0))
                            if pd.notna(latest_income.get("Net Income", 0))
                            else 0
                        ),
                        "gross_profit": (
                            float(latest_income.get("Gross Profit", 0))
                            if pd.notna(latest_income.get("Gross Profit", 0))
                            else 0
                        ),
                    }
                )

            if not balance_sheet.empty:
                latest_balance = balance_sheet.iloc[:, 0]  # 最新一期数据
                result["recent_financials"].update(
                    {
                        "total_assets": (
                            float(latest_balance.get("Total Assets", 0))
                            if pd.notna(latest_balance.get("Total Assets", 0))
                            else 0
                        ),
                        "total_debt": (
                            float(latest_balance.get("Total Debt", 0))
                            if pd.notna(latest_balance.get("Total Debt", 0))
                            else 0
                        ),
                        "shareholders_equity": (
                            float(latest_balance.get("Stockholders Equity", 0))
                            if pd.notna(latest_balance.get("Stockholders Equity", 0))
                            else 0
                        ),
                    }
                )

            if not cash_flow.empty:
                latest_cashflow = cash_flow.iloc[:, 0]  # 最新一期数据
                result["recent_financials"].update(
                    {
                        "operating_cash_flow": (
                            float(latest_cashflow.get("Operating Cash Flow", 0))
                            if pd.notna(latest_cashflow.get("Operating Cash Flow", 0))
                            else 0
                        ),
                        "free_cash_flow": (
                            float(latest_cashflow.get("Free Cash Flow", 0))
                            if pd.notna(latest_cashflow.get("Free Cash Flow", 0))
                            else 0
                        ),
                    }
                )

            logger.info(f"成功获取并精简{ticker}的财务数据，减少token消耗")
            return result
        except Exception as e:
            logger.error(f"获取财务报表失败: {str(e)}")
            raise