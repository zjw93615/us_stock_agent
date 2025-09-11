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
            parameters={
                "ticker": {"type": "str", "description": "股票代码，如AAPL"},
                "period": {"type": "str", "description": "财报周期，可选值：'annual'(年报)或'quarterly'(季报)，默认为annual", "default": "annual"},
                "num_periods": {"type": "int", "description": "获取财报的期数，1表示最近一期，2-5表示获取多期进行对比分析，默认为1", "default": 1}
            },
        )
    
    def _safe_float_convert(self, value):
        """安全地将值转换为浮点数"""
        import pandas as pd
        try:
            if pd.isna(value) or value is None:
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def run(self, ticker: str, period: str = "annual", num_periods: int = 1) -> Dict:
        # 实际实现中调用之前的StockDataFetcher
        logger.info(f"获取财务报表: 股票={ticker}, 周期={period}, 期数={num_periods}")
        import yfinance as yf
        import pandas as pd

        # 验证参数
        if period not in ["annual", "quarterly"]:
            period = "annual"
        if num_periods < 1 or num_periods > 5:
            num_periods = 1

        stock = yf.Ticker(ticker)
        try:
            # 根据period参数获取对应的财务数据
            try:
                if period == "quarterly":
                    balance_sheet = stock.quarterly_balance_sheet
                    income_stmt = stock.quarterly_income_stmt
                    cash_flow = stock.quarterly_cashflow
                    financials = stock.quarterly_financials
                else:
                    balance_sheet = stock.balance_sheet
                    income_stmt = stock.income_stmt
                    cash_flow = stock.cashflow
                    financials = stock.financials
                
                info = stock.info
            except Exception as e:
                logger.warning(f"获取{ticker}财务数据时出现警告: {str(e)}")
                # 初始化空的DataFrame以防止后续错误
                balance_sheet = pd.DataFrame()
                income_stmt = pd.DataFrame()
                cash_flow = pd.DataFrame()
                financials = pd.DataFrame()
                info = {}

            # 计算增长率指标
            earnings_growth = "N/A"
            dividend_growth = "N/A"
            
            # 计算收益增长率（基于最近两年的净收入）
            if not income_stmt.empty and income_stmt.shape[1] >= 2:
                try:
                    current_earnings = income_stmt.iloc[:, 0].get("Net Income", 0)
                    previous_earnings = income_stmt.iloc[:, 1].get("Net Income", 0)
                    if (pd.notna(current_earnings) and pd.notna(previous_earnings) and 
                        previous_earnings != 0 and current_earnings != 0):
                        earnings_growth = ((current_earnings - previous_earnings) / abs(previous_earnings)) * 100
                        earnings_growth = round(earnings_growth, 2)
                except (Exception, ZeroDivisionError, TypeError):
                    earnings_growth = "N/A"
            
            # 计算股息增长率（基于历史股息数据）
            try:
                dividends = stock.dividends
                if not dividends.empty and len(dividends) >= 2:
                    # 获取最近两年的年度股息
                    yearly_dividends = dividends.resample('YE').sum()
                    if len(yearly_dividends) >= 2:
                        current_div = yearly_dividends.iloc[-1]
                        previous_div = yearly_dividends.iloc[-2]
                        if (pd.notna(current_div) and pd.notna(previous_div) and 
                            current_div > 0 and previous_div > 0):
                            dividend_growth = ((current_div - previous_div) / previous_div) * 100
                            dividend_growth = round(dividend_growth, 2)
            except (Exception, ZeroDivisionError, TypeError):
                dividend_growth = "N/A"

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
                    "beta": info.get("beta", "N/A"),  # 相对市场的风险系数
                    "earnings_growth": earnings_growth,  # 收益增长率（%）
                    "dividend_growth": dividend_growth,  # 股息增长率（%）
                    # 从stock.financials获取的关键指标
                    "earnings_per_share": info.get("trailingEps", "N/A"),  # 每股收益
                    "book_value_per_share": info.get("bookValue", "N/A"),  # 每股账面价值
                    "dividend_per_share": info.get("dividendRate", "N/A"),  # 每股股息
                },
                "recent_financials": {},
            }

            # 根据num_periods参数提取财务数据
            if num_periods > 1:
                # 获取多期数据进行对比
                result["historical_financials"] = []
                # 确保periods_to_get不会超过可用数据的最小值
                max_periods_income = income_stmt.shape[1] if not income_stmt.empty else 0
                max_periods_balance = balance_sheet.shape[1] if not balance_sheet.empty else 0
                max_periods_cash = cash_flow.shape[1] if not cash_flow.empty else 0
                max_periods_financials = financials.shape[1] if not financials.empty else 0
                
                max_available_periods = max(max_periods_income, max_periods_balance, max_periods_cash, max_periods_financials)
                periods_to_get = min(num_periods, max_available_periods) if max_available_periods > 0 else 0
                
                for i in range(periods_to_get):
                    period_data = {"period_index": i, "date": str(income_stmt.columns[i]) if not income_stmt.empty and i < len(income_stmt.columns) else "N/A"}
                    
                    if not income_stmt.empty and i < income_stmt.shape[1]:
                        period_income = income_stmt.iloc[:, i]
                        period_data.update({
                            "total_revenue": self._safe_float_convert(period_income.get("Total Revenue", 0)),
                            "net_income": self._safe_float_convert(period_income.get("Net Income", 0)),
                            "gross_profit": self._safe_float_convert(period_income.get("Gross Profit", 0)),
                        })
                    
                    if not balance_sheet.empty and i < balance_sheet.shape[1]:
                        period_balance = balance_sheet.iloc[:, i]
                        period_data.update({
                            "total_assets": self._safe_float_convert(period_balance.get("Total Assets", 0)),
                            "total_debt": self._safe_float_convert(period_balance.get("Total Debt", 0)),
                            "shareholders_equity": self._safe_float_convert(period_balance.get("Stockholders Equity", 0)),
                        })
                    
                    if not cash_flow.empty and i < cash_flow.shape[1]:
                        period_cashflow = cash_flow.iloc[:, i]
                        period_data.update({
                            "operating_cash_flow": self._safe_float_convert(period_cashflow.get("Operating Cash Flow", 0)),
                            "free_cash_flow": self._safe_float_convert(period_cashflow.get("Free Cash Flow", 0)),
                        })
                    
                    # 添加financials数据到历史财务数据中
                    if not financials.empty and i < financials.shape[1]:
                        period_financials = financials.iloc[:, i]
                        period_data.update({
                            "ebitda": self._safe_float_convert(period_financials.get("EBITDA", 0)),
                            "interest_expense": self._safe_float_convert(period_financials.get("Interest Expense", 0)),
                            "tax_provision": self._safe_float_convert(period_financials.get("Tax Provision", 0)),
                        })
                    
                    result["historical_financials"].append(period_data)
                
            # 同时保留最近一期的数据在recent_financials中
            if not income_stmt.empty:
                latest_income = income_stmt.iloc[:, 0]
                result["recent_financials"].update(
                    {
                        "total_revenue": self._safe_float_convert(latest_income.get("Total Revenue", 0)),
                        "net_income": self._safe_float_convert(latest_income.get("Net Income", 0)),
                        "gross_profit": self._safe_float_convert(latest_income.get("Gross Profit", 0)),
                    }
                )

            # 处理资产负债表和现金流量表数据（避免重复代码）
            if not balance_sheet.empty:
                latest_balance = balance_sheet.iloc[:, 0]  # 最新一期数据
                result["recent_financials"].update(
                    {
                        "total_assets": self._safe_float_convert(latest_balance.get("Total Assets", 0)),
                        "total_debt": self._safe_float_convert(latest_balance.get("Total Debt", 0)),
                        "shareholders_equity": self._safe_float_convert(latest_balance.get("Stockholders Equity", 0)),
                    }
                )

            if not cash_flow.empty:
                latest_cashflow = cash_flow.iloc[:, 0]  # 最新一期数据
                result["recent_financials"].update(
                    {
                        "operating_cash_flow": self._safe_float_convert(latest_cashflow.get("Operating Cash Flow", 0)),
                        "free_cash_flow": self._safe_float_convert(latest_cashflow.get("Free Cash Flow", 0)),
                    }
                )

            # 从financials中提取额外的财务指标
            if not financials.empty:
                latest_financials = financials.iloc[:, 0]  # 最新一期数据
                result["recent_financials"].update(
                    {
                        "ebitda": self._safe_float_convert(latest_financials.get("EBITDA", 0)),
                        "interest_expense": self._safe_float_convert(latest_financials.get("Interest Expense", 0)),
                        "tax_provision": self._safe_float_convert(latest_financials.get("Tax Provision", 0)),
                    }
                )

            # 添加元数据信息
            # result["metadata"] = {
            #     "period_type": period,
            #     "num_periods_requested": num_periods,
            #     "num_periods_returned": len(result.get("historical_financials", [])) if num_periods > 1 else 1,
            #     "data_availability": {
            #         "income_statement": not income_stmt.empty,
            #         "balance_sheet": not balance_sheet.empty,
            #         "cash_flow": not cash_flow.empty,
            #         "financials": not financials.empty
            #     }
            # }
            
            # 检查是否获取到任何有效数据
            has_any_data = (not income_stmt.empty or not balance_sheet.empty or 
                          not cash_flow.empty or not financials.empty or bool(info))
            
            if not has_any_data:
                logger.warning(f"未能获取到{ticker}的任何财务数据")
                result["warning"] = "未能获取到有效的财务数据，可能是股票代码无效或数据暂时不可用"
            
            logger.info(f"成功获取并精简{ticker}的财务数据，周期={period}，期数={num_periods}，减少token消耗")
            return result
        except Exception as e:
            logger.error(f"获取财务报表失败: {str(e)}")
            raise