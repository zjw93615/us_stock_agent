import os
import json
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from langchain.tools import tool
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langgraph.graph import Graph, END
import requests

# 配置API密钥（实际使用时替换为你的密钥）
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
NEWS_API_KEY = "your-news-api-key"

# ------------------------------
# 1. 工具定义 - 信息获取模块
# ------------------------------
class StockTools:
    @tool("获取股票基本信息")
    def get_stock_basic_info(ticker: str) -> dict:
        """获取股票的基本信息，包括公司名称、行业、市值等"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                "company_name": info.get("longName"),
                "industry": info.get("industry"),
                "market_cap_bil": info.get("marketCap", 0) / 1e8,
                "forward_pe": info.get("forwardPE"),
                "price_to_book": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            }
        except Exception as e:
            return f"获取股票基本信息失败: {str(e)}"
    
    @tool("获取财务报表数据")
    def get_financial_statements(ticker: str, statement_type: str = "income") -> dict:
        """
        获取公司财务报表数据
        statement_type: 可选值 'income'(利润表), 'balance'(资产负债表), 'cash'(现金流量表)
        """
        try:
            stock = yf.Ticker(ticker)
            
            if statement_type == "income":
                statements = stock.income_stmt
            elif statement_type == "balance":
                statements = stock.balance_sheet
            elif statement_type == "cash":
                statements = stock.cash_flow
            else:
                return "无效的报表类型"
                
            # 转换为字典并保留最近3年数据
            result = [] if isinstance(statements, list) else {}
            for date in statements.columns[:3]:
                result[str(date.date())] = {
                    index: float(value) for index, value in statements[date].dropna().items()
                }
            return result
        except Exception as e:
            return f"获取财务报表失败: {str(e)}"
    
    @tool("获取相关新闻")
    def get_related_news(ticker: str) -> list:
        """获取与该股票相关的最新新闻"""
        try:
            # 使用新闻API获取相关新闻（此处为示例，实际需替换为真实API）
            url = f"https://newsapi.org/v2/everything?q={ticker}&apiKey={NEWS_API_KEY}&pageSize=5"
            response = requests.get(url)
            news = response.json()
            
            if news.get("status") == "ok":
                return [
                    {
                        "title": item["title"],
                        "source": item["source"]["name"],
                        "published_at": item["publishedAt"],
                        "url": item["url"],
                    } 
                    for item in news["articles"]
                ]
            return ["未获取到相关新闻"]
        except Exception as e:
            return f"获取新闻失败: {str(e)}"
    
    @tool("获取可比公司列表")
    def get_peer_companies(ticker: str) -> list:
        """获取与该公司业务相似的可比公司列表"""
        try:
            stock = yf.Ticker(ticker)
            peers = stock.info.get("sectorPeers", [])
            # 如果没有行业 peers，返回同行业知名公司（示例）
            if not peers:
                industry = stock.info.get("industry", "")
                if "technology" in industry.lower():
                    return ["AAPL", "MSFT", "GOOGL"]
                elif "financial" in industry.lower():
                    return ["JPM", "BAC", "WFC"]
                else:
                    return []
            return peers[:5]  # 限制返回5个可比公司
        except Exception as e:
            return f"获取可比公司失败: {str(e)}"

# ------------------------------
# 2. 估值计算模块
# ------------------------------
class ValuationCalculator:
    @staticmethod
    def calculate_dcf(financial_data: dict, growth_rate: float = 0.05, discount_rate: float = 0.1) -> dict:
        """
        现金流折现法(DCF)计算公司价值
        financial_data: 包含现金流量表数据的字典
        growth_rate: 永续增长率
        discount_rate: 折现率
        """
        try:
            # 提取最近3年的经营现金流
            cash_flows = []
            dates = sorted(financial_data.keys())
            
            for date in dates:
                stmt = financial_data[date]
                # 寻找经营现金流相关项目（不同公司可能有不同的命名）
                cf_items = [key for key in stmt if "cash flow from operating" in key.lower()]
                if cf_items:
                    cash_flows.append(stmt[cf_items[0]])
            
            if not cash_flows:
                return {"error": "无法获取经营现金流数据"}
            
            # 预测未来5年现金流
            projected_cf = []
            current_cf = cash_flows[0]  # 使用最近一年的现金流
            for i in range(5):
                # 前3年增长率递减，后2年保持稳定
                if i < 3:
                    growth = growth_rate * (1 - i * 0.2)
                else:
                    growth = growth_rate
                projected_cf.append(current_cf * (1 + growth))
                current_cf = projected_cf[-1]
            
            # 计算终端价值
            terminal_value = projected_cf[-1] * (1 + growth_rate) / (discount_rate - growth_rate)
            
            # 计算现值
            present_values = []
            for i, cf in enumerate(projected_cf):
                present_values.append(cf / ((1 + discount_rate) ** (i + 1)))
            
            # 加上终端价值的现值
            present_values.append(terminal_value / ((1 + discount_rate) ** 5))
            
            # 计算总价值
            total_value = sum(present_values)
            
            return {
                "predicted_cash_flows": [round(cf, 2) for cf in projected_cf],
                "terminal_value": round(terminal_value, 2),
                "discount_rate": discount_rate,
                "perpetual_growth_rate": growth_rate,
                "enterprise_value_bil": round(total_value / 1e8, 2),
                "per_share_value_dcf": round(total_value / 1e8 / 1e4, 2),  # 简化计算
            }
        except Exception as e:
            return {"error": f"DCF计算失败: {str(e)}"}
    
    @staticmethod
    def calculate_relative_valuation(ticker: str, peers: list, stock_info: dict) -> dict:
        """
        相对估值法计算公司价值
        """
        try:
            # 获取可比公司的估值指标
            peer_data = []
            for peer in peers:
                try:
                    p_info = yf.Ticker(peer).info
                    peer_data.append({
                        "company": peer,
                        "pe": p_info.get("forwardPE"),
                        "pb": p_info.get("priceToBook"),
                        "ps": p_info.get("priceToSalesTrailing12Months"),
                    })
                except Exception:
                    continue
            
            if not peer_data:
                return {"error": "无法获取可比公司数据"}
            
            # 计算平均估值指标
            avg_pe = np.mean([d["pe"] for d in peer_data if d["pe"] and d["pe"] > 0])
            avg_pb = np.mean([d["pb"] for d in peer_data if d["pb"] and d["pb"] > 0])
            avg_ps = np.mean([d["ps"] for d in peer_data if d["ps"] and d["ps"] > 0])
            
            # 获取目标公司财务数据
            stock = yf.Ticker(ticker)
            financials = stock.income_stmt
            latest_date = financials.columns[0] if not financials.empty else None
            
            # 计算相对估值
            valuation = {}
            if latest_date and not np.isnan(avg_pe):
                eps = financials.loc["Diluted EPS", latest_date] if "Diluted EPS" in financials.index else None
                if eps:
                    valuation["price_target_by_pe"] = round(avg_pe * eps, 2)
            
            if not np.isnan(avg_pb):
                bvps = stock.info.get("bookValue")
                if bvps:
                    valuation["price_target_by_pb"] = round(avg_pb * bvps, 2)
            
            if latest_date and not np.isnan(avg_ps):
                revenue_per_share = (
                    financials.loc["Total Revenue", latest_date] / stock.info.get("sharesOutstanding", 1)
                    if "Total Revenue" in financials.index
                    else None
                )
                if revenue_per_share:
                    valuation["price_target_by_ps"] = round(avg_ps * revenue_per_share, 2)
            
            return {
                "peer_count": len(peer_data),
                "avg_pe": round(avg_pe, 2) if not np.isnan(avg_pe) else None,
                "avg_pb": round(avg_pb, 2) if not np.isnan(avg_pb) else None,
                "avg_ps": round(avg_ps, 2) if not np.isnan(avg_ps) else None,
                "relative_valuation": valuation,
            }
        except Exception as e:
            return {"error": f"相对估值计算失败: {str(e)}"}

# ------------------------------
# 3. LangGraph 工作流定义
# ------------------------------
class StockValuationGraph:
    def __init__(self):
        self.tools = StockTools()
        self.calculator = ValuationCalculator()
        self.llm = OpenAI(temperature=0.2)
        
        # 创建图
        self.graph = Graph()
        
        # 定义节点
        self.graph.add_node("获取股票基本信息", self.get_basic_info_node)
        self.graph.add_node("获取财务数据", self.get_financial_data_node)
        self.graph.add_node("获取可比公司", self.get_peer_companies_node)
        self.graph.add_node("获取相关新闻", self.get_news_node)
        self.graph.add_node("计算绝对估值", self.calculate_absolute_valuation_node)
        self.graph.add_node("计算相对估值", self.calculate_relative_valuation_node)
        self.graph.add_node("整合结果", self.summary_node)
        
        # 定义边
        self.graph.set_entry_point("获取股票基本信息")
        self.graph.add_edge("获取股票基本信息", "获取财务数据")
        self.graph.add_edge("获取财务数据", "获取可比公司")
        self.graph.add_edge("获取可比公司", "获取相关新闻")
        self.graph.add_edge("获取相关新闻", "计算绝对估值")
        self.graph.add_edge("计算绝对估值", "计算相对估值")
        self.graph.add_edge("计算相对估值", "整合结果")
        self.graph.add_edge("整合结果", END)
        
        # 编译图
        self.app = self.graph.compile()
    
    def get_basic_info_node(self, state):
        ticker = state.get("ticker")
        info = self.tools.get_stock_basic_info(ticker)
        return {"basic_info": info, "ticker": ticker}
    
    def get_financial_data_node(self, state):
        ticker = state.get("ticker")
        income = self.tools.get_financial_statements(ticker, "income")
        cash_flow = self.tools.get_financial_statements(ticker, "cash")
        return {**state, "income_statement": income, "cash_flow_statement": cash_flow}
    
    def get_peer_companies_node(self, state):
        ticker = state.get("ticker")
        peers = self.tools.get_peer_companies(ticker)
        return {**state, "peer_companies": peers}
    
    def get_news_node(self, state):
        ticker = state.get("ticker")
        news = self.tools.get_related_news(ticker)
        return {**state, "related_news": news}
    
    def calculate_absolute_valuation_node(self, state):
        cash_flow = state.get("cash_flow_statement")
        dcf_result = self.calculator.calculate_dcf(cash_flow)
        return {**state, "absolute_valuation": dcf_result}
    
    def calculate_relative_valuation_node(self, state):
        ticker = state.get("ticker")
        peers = state.get("peer_companies")
        basic_info = state.get("basic_info")
        relative_result = self.calculator.calculate_relative_valuation(ticker, peers, basic_info)
        return {**state, "relative_valuation": relative_result}
    
    def summary_node(self, state):
        """整合所有信息，生成最终估值报告"""
        prompt = PromptTemplate(
            template="""请基于以下信息，生成一份股票估值报告：
            1. 基本信息：{basic_info}
            2. 绝对估值（DCF）：{absolute_valuation}
            3. 相对估值：{relative_valuation}
            4. 相关新闻：{related_news}
            
            报告应包括估值总结、目标价格范围、投资建议及风险提示。
            """,
            input_variables=["basic_info", "absolute_valuation", "relative_valuation", "related_news"]
        )
        
        report = self.llm(prompt.format(
            basic_info=json.dumps(state["basic_info"], ensure_ascii=False),
            absolute_valuation=json.dumps(state["absolute_valuation"], ensure_ascii=False),
            relative_valuation=json.dumps(state["relative_valuation"], ensure_ascii=False),
            related_news=json.dumps(state["related_news"], ensure_ascii=False)
        ))
        
        return {**state, "final_report": report}
    
    def run(self, ticker):
        """运行估值流程"""
        result = self.app.invoke({"ticker": ticker})
        return result["final_report"]

# ------------------------------
# 4. 使用示例
# ------------------------------
if __name__ == "__main__":
    # 初始化估值系统
    valuation_system = StockValuationGraph()
    
    # 对苹果公司(AAPL)进行估值
    ticker = "AAPL"
    print(f"正在对 {ticker} 进行估值分析...")
    report = valuation_system.run(ticker)
    
    # 输出结果
    print("\n===== 股票估值报告 =====")
    print(report)
