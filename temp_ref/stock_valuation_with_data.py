import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, Optional, Union

class StockValuationTool:
    """股票估值工具，整合多种估值方法和数据获取功能"""
    
    def __init__(self, ticker: str):
        """初始化估值工具并获取股票基本数据"""
        self.ticker = ticker
        self.stock = yf.Ticker(ticker)
        self.results = {}
        self.financial_data = self._fetch_financial_data()
        self.industry_data = self._fetch_industry_data()
        
    def _fetch_financial_data(self) -> Dict:
        """获取股票的财务数据"""
        try:
            # 获取基本信息
            info = self.stock.info
            
            # 获取财务报表数据
            financials = self.stock.financials
            balance_sheet = self.stock.balance_sheet
            cashflow = self.stock.cashflow
            
            # 提取关键财务指标
            return {
                # 基本信息
                'sector': info.get('sector', '未知'),
                'industry': info.get('industry', '未知'),
                'market_cap': info.get('marketCap', 0),
                
                # 每股指标
                'earnings_per_share': info.get('trailingEps', 0),
                'book_value_per_share': info.get('bookValue', 0),
                'dividend_per_share': info.get('dividendRate', 0),
                
                # 盈利能力指标
                'roe': info.get('returnOnEquity', 0),
                
                # 增长率
                'earnings_growth': info.get('earningsGrowth', 0),
                'dividend_growth': info.get('fiveYearAvgDividendYield', 0) / 100 if info.get('fiveYearAvgDividendYield') else 0,
                
                # 自由现金流(最近一期)
                'free_cash_flow': cashflow.loc['Free Cash Flow'].iloc[0] if 'Free Cash Flow' in cashflow.index else 0,
                
                # 市盈率和市净率
                'pe_ratio': info.get('trailingPE', 0),
                'pb_ratio': info.get('priceToBook', 0),
                
                # 风险指标
                'beta': info.get('beta', 1.0)  # 相对市场的风险系数
            }
        except Exception as e:
            print(f"获取财务数据时出错: {e}")
            return {}
    
    def _fetch_industry_data(self) -> Dict:
        """获取行业平均数据作为参考"""
        try:
            # 在实际应用中，这里可以连接更专业的数据源获取行业平均数据
            # 这里使用简化版，基于个股数据和一些假设
            info = self.stock.info
            
            # 对于演示，我们使用雅虎财经提供的行业平均数据或合理假设
            return {
                'industry_pe': info.get('industryTrailingPE', info.get('trailingPE', 15) * 1.1),
                'industry_pb': info.get('industryPriceToBook', info.get('priceToBook', 1.5) * 1.1),
                'industry_roe': info.get('industryReturnOnEquity', self.financial_data.get('roe', 0.15) * 0.9)
            }
        except Exception as e:
            print(f"获取行业数据时出错: {e}")
            return {}
    
    def calculate_discount_rate(self, risk_free_rate: float = 0.03) -> float:
        """
        计算贴现率(使用CAPM模型)
        
        参数:
            risk_free_rate: 无风险利率，默认为3%
            
        返回:
            计算得到的贴现率
        """
        # 假设市场风险溢价为6%
        market_risk_premium = 0.06
        beta = self.financial_data.get('beta', 1.0)
        
        # CAPM模型: 贴现率 = 无风险利率 + β*(市场风险溢价)
        discount_rate = risk_free_rate + beta * market_risk_premium
        return discount_rate
    
    def pe_valuation(self, company_risk_factor: Optional[float] = None) -> float:
        """
        市盈率(PE)估值法，使用自动获取的数据
        
        参数:
            company_risk_factor: 公司风险因子，默认基于beta计算
            
        返回:
            估值价格
        """
        # 如果未提供风险因子，则基于beta计算
        if company_risk_factor is None:
            # beta为1表示与市场风险相同，beta越大风险越高
            company_risk_factor = min(1.5, max(0.5, self.financial_data.get('beta', 1.0) * 0.8))
        
        earnings_per_share = self.financial_data.get('earnings_per_share', 0)
        industry_pe = self.industry_data.get('industry_pe', 15)
        
        if earnings_per_share <= 0:
            raise ValueError("每股收益必须为正数")
        if industry_pe <= 0:
            raise ValueError("行业市盈率必须为正数")
        
        # 根据公司风险调整市盈率
        adjusted_pe = industry_pe * company_risk_factor
        price = earnings_per_share * adjusted_pe
        
        self.results['PE估值'] = {
            '每股收益': earnings_per_share,
            '行业市盈率': industry_pe,
            '风险调整因子': company_risk_factor,
            '调整后市盈率': adjusted_pe,
            '估值价格': price
        }
        
        return price
    
    def pb_valuation(self) -> float:
        """
        市净率(PB)估值法，使用自动获取的数据
        
        返回:
            估值价格
        """
        book_value_per_share = self.financial_data.get('book_value_per_share', 0)
        industry_pb = self.industry_data.get('industry_pb', 1.5)
        roe = self.financial_data.get('roe', 0)
        industry_roe = self.industry_data.get('industry_roe', 0.15)
        
        if book_value_per_share <= 0:
            raise ValueError("每股净资产必须为正数")
        if industry_pb <= 0:
            raise ValueError("行业市净率必须为正数")
        if industry_roe <= 0:
            raise ValueError("行业平均净资产收益率必须为正数")
        
        # 根据ROE相对水平调整市净率
        roe_factor = roe / industry_roe if industry_roe != 0 else 1.0
        adjusted_pb = industry_pb * roe_factor
        price = book_value_per_share * adjusted_pb
        
        self.results['PB估值'] = {
            '每股净资产': book_value_per_share,
            '行业市净率': industry_pb,
            '公司ROE': roe,
            '行业平均ROE': industry_roe,
            'ROE因子': roe_factor,
            '调整后市净率': adjusted_pb,
            '估值价格': price
        }
        
        return price
    
    def ddm_valuation(self, 
                     high_growth_period: int = 5,
                     stable_growth_rate: Optional[float] = None) -> float:
        """
        股利贴现模型(DDM)估值，使用自动获取的数据
        
        参数:
            high_growth_period: 高增长期年限
            stable_growth_rate: 稳定增长期的增长率，默认为股息增长率的一半
            
        返回:
            估值价格
        """
        current_dividend = self.financial_data.get('dividend_per_share', 0)
        growth_rate = self.financial_data.get('dividend_growth', 0.05)
        discount_rate = self.calculate_discount_rate()
        
        if current_dividend <= 0:
            raise ValueError("当前股息必须为正数，不支付股息的公司不适合DDM模型")
        if growth_rate >= discount_rate:
            raise ValueError("股息增长率必须小于贴现率")
        
        # 如果未提供稳定增长率，默认设为高增长率的一半
        if stable_growth_rate is None:
            stable_growth_rate = max(0.02, growth_rate / 2)
            
        if stable_growth_rate >= discount_rate:
            raise ValueError("稳定增长率必须小于贴现率")
        
        # 计算高增长期的股息现值
        high_growth_pv = 0
        for year in range(1, high_growth_period + 1):
            dividend = current_dividend * (1 + growth_rate) ** year
            pv = dividend / (1 + discount_rate) ** year
            high_growth_pv += pv
        
        # 计算稳定增长期的股息现值(永续增长模型)
        final_dividend = current_dividend * (1 + growth_rate) ** high_growth_period
        stable_dividend = final_dividend * (1 + stable_growth_rate)
        terminal_value = stable_dividend / (discount_rate - stable_growth_rate)
        terminal_value_pv = terminal_value / (1 + discount_rate) ** high_growth_period
        
        # 总估值
        price = high_growth_pv + terminal_value_pv
        
        self.results['DDM估值'] = {
            '当前股息': current_dividend,
            '高增长率': growth_rate,
            '稳定增长率': stable_growth_rate,
            '贴现率': discount_rate,
            '高增长期(年)': high_growth_period,
            '高增长期现值': high_growth_pv,
            '终值现值': terminal_value_pv,
            '估值价格': price
        }
        
        return price
    
    def dcf_valuation(self, 
                    years: int = 5,
                    terminal_growth_rate: float = 0.03) -> float:
        """
        现金流折现法(DCF)估值，使用自动获取的数据
        
        参数:
            years: 预测年数
            terminal_growth_rate: 终值阶段增长率，默认为3%
            
        返回:
            估值价格
        """
        current_fcf = self.financial_data.get('free_cash_flow', 0)
        earnings_growth = self.financial_data.get('earnings_growth', 0.08)
        discount_rate = self.calculate_discount_rate()
        
        if current_fcf <= 0:
            raise ValueError("当前自由现金流必须为正数")
        if terminal_growth_rate >= discount_rate:
            raise ValueError("终值增长率必须小于贴现率")
        
        # 假设增长率逐年递减至稳定水平
        growth_rates = [earnings_growth * (1 - i/(years*2)) for i in range(years)]
        
        # 计算预测期现金流现值
        fcf_pv = 0
        for year in range(1, years + 1):
            fcf = current_fcf * np.prod([1 + r for r in growth_rates[:year]])
            pv = fcf / (1 + discount_rate) ** year
            fcf_pv += pv
        
        # 计算终值(永续增长模型)
        final_fcf = current_fcf * np.prod([1 + r for r in growth_rates])
        terminal_value = final_fcf * (1 + terminal_growth_rate) / (discount_rate - terminal_growth_rate)
        terminal_value_pv = terminal_value / (1 + discount_rate) ** years
        
        # 总企业价值
        enterprise_value = fcf_pv + terminal_value_pv
        
        # 计算每股价值(假设全为普通股)
        shares_outstanding = self.financial_data.get('market_cap', 0) / self.get_current_price() if self.get_current_price() > 0 else 0
        price_per_share = enterprise_value / shares_outstanding if shares_outstanding > 0 else 0
        
        self.results['DCF估值'] = {
            '当前自由现金流': current_fcf,
            '各年增长率': growth_rates,
            '贴现率': discount_rate,
            '终值增长率': terminal_growth_rate,
            '预测年数': years,
            '预测期现值': fcf_pv,
            '终值现值': terminal_value_pv,
            '企业价值': enterprise_value,
            '每股价值': price_per_share
        }
        
        return price_per_share
    
    def get_current_price(self) -> float:
        """获取当前股票价格"""
        try:
            return self.stock.history(period='1d')['Close'].iloc[-1]
        except:
            return self.financial_data.get('regularMarketPrice', 0)
    
    def get_summary(self) -> pd.DataFrame:
        """
        获取所有估值结果的汇总
        
        返回:
            包含所有估值结果的DataFrame
        """
        if not self.results:
            raise ValueError("尚未进行任何估值计算")
        
        current_price = self.get_current_price()
        summary_data = []
        
        for method, details in self.results.items():
            # 从详细结果中获取估值价格，不同方法的键名可能不同
            price_key = '估值价格' if '估值价格' in details else '每股价值'
            valuation_price = details[price_key]
            
            row = {
                '估值方法': method,
                '估值价格': valuation_price,
                '当前市场价格': current_price,
            }
            
            if current_price > 0:
                row['与市场价比率'] = valuation_price / current_price
                row['溢价/折价'] = '溢价' if valuation_price > current_price else '折价'
            
            summary_data.append(row)
        
        return pd.DataFrame(summary_data)


# 使用示例
if __name__ == "__main__":
    # 创建估值工具实例，指定股票代码(例如苹果公司: AAPL)
    ticker = "AAPL"  # 可以更换为其他股票代码，如"MSFT"、"GOOG"等
    valuer = StockValuationTool(ticker)
    
    print(f"正在评估股票: {ticker}")
    print(f"行业: {valuer.financial_data.get('industry', '未知')}")
    print(f"当前价格: {valuer.get_current_price():.2f}元")
    print(f"计算得到的贴现率: {valuer.calculate_discount_rate():.2%}")
    print("----------------------------------------")
    
    # 1. 市盈率估值
    try:
        pe_price = valuer.pe_valuation()
        print(f"市盈率估值价格: {pe_price:.2f}元")
    except ValueError as e:
        print(f"市盈率估值出错: {e}")
    
    # 2. 市净率估值
    try:
        pb_price = valuer.pb_valuation()
        print(f"市净率估值价格: {pb_price:.2f}元")
    except ValueError as e:
        print(f"市净率估值出错: {e}")
    
    # 3. 股利贴现模型估值
    try:
        ddm_price = valuer.ddm_valuation(high_growth_period=5)
        print(f"股利贴现模型估值价格: {ddm_price:.2f}元")
    except ValueError as e:
        print(f"股利贴现模型估值出错: {e}")
    
    # 4. 现金流折现法估值
    try:
        dcf_price = valuer.dcf_valuation(years=5)
        print(f"现金流折现法估值价格: {dcf_price:.2f}元")
    except ValueError as e:
        print(f"现金流折现法估值出错: {e}")
    
    # 打印汇总结果
    try:
        print("\n估值结果汇总:")
        summary = valuer.get_summary()
        print(summary.round(2))
    except Exception as e:
        print(f"生成汇总结果时出错: {e}")
    