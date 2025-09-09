import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class DCFModel:
    def __init__(self, ticker):
        """初始化DCF模型，获取基本财务数据"""
        self.ticker = ticker
        self.stock = yf.Ticker(ticker)
        self.years = 5  # 默认预测5年
        
        # 获取财务数据
        self.financials = self.stock.financials
        self.balance_sheet = self.stock.balance_sheet
        self.cashflow = self.stock.cashflow
        
        # 获取市场数据
        self.info = self.stock.info
        
        # 计算WACC所需数据
        self.risk_free_rate = self._get_risk_free_rate()
        self.market_risk_premium = 0.07  # 市场风险溢价，通常取5%-7%
        
    def _get_risk_free_rate(self):
        """获取10年期美国国债收益率作为无风险利率"""
        try:
            # 获取10年期美国国债数据
            treasury = yf.Ticker("^TNX")  # ^TNX是10年期美国国债收益率
            hist = treasury.history(period="1d")
            return hist['Close'].iloc[-1] / 100  # 转换为小数
        except:
            return 0.03  # 无法获取时使用默认值3%
    
    def calculate_wacc(self, tax_rate=0.21):
        """计算加权平均资本成本(WACC)"""
        try:
            # 获取贝塔系数
            beta = self.info.get('beta', 1.0)
            
            # 股权成本 (CAPM模型)
            cost_of_equity = self.risk_free_rate + beta * self.market_risk_premium
            
            # 获取债务和股权数据
            total_debt = self.balance_sheet.loc['Total Debt', self.balance_sheet.columns[0]]
            market_cap = self.info.get('marketCap', 0)
            total_value = total_debt + market_cap
            
            if total_value == 0:
                return cost_of_equity  # 无法计算时使用股权成本
            
            # 债务成本 (处理NA情况)
            try:
                # 尝试获取最新的利息支出
                interest_expense = self.financials.loc['Interest Expense', self.financials.columns[0]]
                
                # 检查是否为NA
                if pd.isna(interest_expense):
                    # 方法1：尝试获取历史平均利息支出率
                    historical_rates = []
                    for i in range(1, min(4, len(self.financials.columns))):
                        try:
                            hist_interest = self.financials.loc['Interest Expense', self.financials.columns[i]]
                            hist_debt = self.balance_sheet.loc['Total Debt', self.balance_sheet.columns[i]]
                            if not pd.isna(hist_interest) and not pd.isna(hist_debt) and hist_debt > 0:
                                historical_rates.append(abs(hist_interest) / hist_debt)
                        except:
                            pass
                    
                    if historical_rates:
                        # 使用历史平均利息支出率
                        cost_of_debt = sum(historical_rates) / len(historical_rates)
                        print(f"使用历史平均利息支出率: {cost_of_debt:.2%}")
                    else:
                        # 方法2：使用公司债券收益率估算
                        cost_of_debt = self.risk_free_rate + 0.02  # 无风险利率 + 2%作为信用息差
                        print(f"使用估算的债券收益率: {cost_of_debt:.2%}")
                else:
                    cost_of_debt = abs(interest_expense) / total_debt if total_debt > 0 else 0
            except Exception as e:
                print(f"计算债务成本时出错: {e}")
                # 方法3：使用行业平均债务成本或估算值
                cost_of_debt = self.risk_free_rate + 0.02  # 无风险利率 + 2%作为信用息差
            
            # 计算WACC
            wacc = (market_cap / total_value) * cost_of_equity + \
                   (total_debt / total_value) * cost_of_debt * (1 - tax_rate)
            
            return wacc
        except Exception as e:
            print(f"计算WACC时出错: {e}")
            return 0.1  # 默认值10%
    
    def generate_cash_flows(self, growth_rates, profit_margins, cap_ex_ratios, working_capital_changes):
        """
        生成未来现金流预测
        
        参数:
        - growth_rates: 收入增长率列表，长度等于预测年数
        - profit_margins: 净利润率列表，长度等于预测年数
        - cap_ex_ratios: 资本支出占收入比例列表，长度等于预测年数
        - working_capital_changes: 营运资本变动占收入比例列表，长度等于预测年数
        """
        # 获取最近一年的收入
        try:
            revenue = self.financials.loc['Total Revenue', self.financials.columns[0]]
        except:
            revenue = self.info.get('totalRevenue', 0)
        
        if revenue == 0:
            raise ValueError("无法获取收入数据，无法进行现金流预测")
        
        # 确保所有参数列表长度与预测年数一致
        if len(growth_rates) != self.years:
            raise ValueError(f"growth_rates长度必须为{self.years}")
        if len(profit_margins) != self.years:
            raise ValueError(f"profit_margins长度必须为{self.years}")
        if len(cap_ex_ratios) != self.years:
            raise ValueError(f"cap_ex_ratios长度必须为{self.years}")
        if len(working_capital_changes) != self.years:
            raise ValueError(f"working_capital_changes长度必须为{self.years}")
        
        cash_flows = []
        current_revenue = revenue
        
        for i in range(self.years):
            # 计算当年收入
            current_revenue *= (1 + growth_rates[i])
            
            # 计算净利润
            net_income = current_revenue * profit_margins[i]
            
            # 计算折旧摊销 (简化处理，使用收入的一定比例)
            depreciation = current_revenue * 0.05  # 假设为收入的5%
            
            # 计算资本支出
            cap_ex = current_revenue * cap_ex_ratios[i]
            
            # 计算营运资本变动
            wc_change = current_revenue * working_capital_changes[i]
            
            # 计算自由现金流
            fcf = net_income + depreciation - cap_ex - wc_change
            cash_flows.append(fcf)
        
        return cash_flows
    
    def calculate_terminal_value(self, last_cash_flow, wacc, terminal_growth_rate):
        """计算终值"""
        return last_cash_flow * (1 + terminal_growth_rate) / (wacc - terminal_growth_rate)
    
    def calculate_intrinsic_value(self, growth_rates, profit_margins, cap_ex_ratios, 
                                working_capital_changes, terminal_growth_rate=0.025):
        """计算公司内在价值"""
        # 计算WACC
        wacc = self.calculate_wacc()
        
        # 生成未来现金流
        cash_flows = self.generate_cash_flows(
            growth_rates, profit_margins, cap_ex_ratios, working_capital_changes
        )
        
        # 计算终值
        terminal_value = self.calculate_terminal_value(cash_flows[-1], wacc, terminal_growth_rate)
        
        # 计算现值
        present_values = []
        for i, cf in enumerate(cash_flows):
            present_value = cf / ((1 + wacc) ** (i + 1))
            present_values.append(present_value)
        
        # 终值现值
        terminal_pv = terminal_value / ((1 + wacc) ** self.years)
        
        # 总企业价值
        enterprise_value = sum(present_values) + terminal_pv
        
        # 减去债务，加上现金及等价物，得到股权价值
        try:
            total_debt = self.balance_sheet.loc['Total Debt', self.balance_sheet.columns[0]]
            cash_and_equivalents = self.balance_sheet.loc['Cash And Cash Equivalents', self.balance_sheet.columns[0]]
        except:
            total_debt = 0
            cash_and_equivalents = 0
        
        equity_value = enterprise_value - total_debt + cash_and_equivalents
        
        # 计算每股价值
        shares_outstanding = self.info.get('sharesOutstanding', 1)
        if shares_outstanding == 0:
            shares_outstanding = 1
            
        intrinsic_value_per_share = equity_value / shares_outstanding
        
        return {
            'wacc': wacc,
            'cash_flows': cash_flows,
            'terminal_value': terminal_value,
            'enterprise_value': enterprise_value,
            'equity_value': equity_value,
            'intrinsic_value_per_share': intrinsic_value_per_share,
            'current_price': self.info.get('currentPrice', None)
        }

# 使用示例
if __name__ == "__main__":
    # 选择一家公司，例如苹果公司
    ticker = "AAPL"
    dcf = DCFModel(ticker)
    
    # 设定预测参数（需要根据行业研究和公司分析进行估算）
    years = 5
    growth_rates = [0.12, 0.10, 0.09, 0.08, 0.07]  # 收入增长率
    profit_margins = [0.25, 0.24, 0.23, 0.22, 0.21]  # 净利润率
    cap_ex_ratios = [0.06, 0.055, 0.05, 0.045, 0.04]  # 资本支出占收入比例
    working_capital_changes = [0.02, 0.015, 0.01, 0.005, 0]  # 营运资本变动占收入比例
    terminal_growth_rate = 0.025  # 终值增长率，通常接近长期GDP增长率
    
    # 计算内在价值
    result = dcf.calculate_intrinsic_value(
        growth_rates, 
        profit_margins, 
        cap_ex_ratios, 
        working_capital_changes, 
        terminal_growth_rate
    )
    
    # 输出结果
    print(f"DCF模型分析结果 for {ticker}:")
    print(f"WACC: {result['wacc']:.2%}")
    print(f"未来{years}年现金流预测: {[f'{cf:,.0f}' for cf in result['cash_flows']]}")
    print(f"终值: ${result['terminal_value']:,.0f}")
    print(f"企业价值: ${result['enterprise_value']:,.0f}")
    print(f"股权价值: ${result['equity_value']:,.0f}")
    print(f"内在价值(每股): ${result['intrinsic_value_per_share']:.2f}")
    print(f"当前股价: ${result['current_price']:.2f}" if result['current_price'] else "无法获取当前股价")
    
    # 评估是否被低估
    if result['current_price']:
        if result['intrinsic_value_per_share'] > result['current_price']:
            print(f"结论: {ticker} 被低估，潜在涨幅: {((result['intrinsic_value_per_share']/result['current_price'])-1):.2%}")
        else:
            print(f"结论: {ticker} 被高估，潜在跌幅: {((result['current_price']/result['intrinsic_value_per_share'])-1):.2%}")