import numpy as np
import pandas as pd
from typing import Dict, Optional, Union

class StockValuationTool:
    """股票估值工具，整合多种估值方法"""
    
    def __init__(self):
        """初始化估值工具"""
        self.results = {}
        
    def pe_valuation(self, 
                    earnings_per_share: float, 
                    industry_pe: float, 
                    company_risk_factor: float = 1.0) -> float:
        """
        市盈率(PE)估值法
        
        参数:
            earnings_per_share: 每股收益(EPS)
            industry_pe: 行业平均市盈率
            company_risk_factor: 公司风险因子，大于1表示风险高于行业平均，小于1表示风险低于行业平均
            
        返回:
            估值价格
        """
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
    
    def pb_valuation(self, 
                    book_value_per_share: float, 
                    industry_pb: float, 
                    roe: float, 
                    industry_roe: float) -> float:
        """
        市净率(PB)估值法
        
        参数:
            book_value_per_share: 每股净资产
            industry_pb: 行业平均市净率
            roe: 公司净资产收益率
            industry_roe: 行业平均净资产收益率
            
        返回:
            估值价格
        """
        if book_value_per_share <= 0:
            raise ValueError("每股净资产必须为正数")
        if industry_pb <= 0:
            raise ValueError("行业市净率必须为正数")
        if industry_roe <= 0:
            raise ValueError("行业平均净资产收益率必须为正数")
        
        # 根据ROE相对水平调整市净率
        roe_factor = roe / industry_roe
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
                     current_dividend: float, 
                     growth_rate: float, 
                     discount_rate: float,
                     high_growth_period: int = 5,
                     stable_growth_rate: float = None) -> float:
        """
        股利贴现模型(DDM)估值
        
        参数:
            current_dividend: 当前股息
            growth_rate: 股息增长率
            discount_rate: 贴现率
            high_growth_period: 高增长期年限
            stable_growth_rate: 稳定增长期的增长率，默认为growth_rate的一半
            
        返回:
            估值价格
        """
        if current_dividend <= 0:
            raise ValueError("当前股息必须为正数")
        if growth_rate >= discount_rate:
            raise ValueError("股息增长率必须小于贴现率")
        
        # 如果未提供稳定增长率，默认设为高增长率的一半
        if stable_growth_rate is None:
            stable_growth_rate = growth_rate / 2
            
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
                    current_fcf: float, 
                    growth_rates: Union[float, list], 
                    discount_rate: float,
                    terminal_growth_rate: float = 0.03,
                    years: int = 5) -> float:
        """
        现金流折现法(DCF)估值
        
        参数:
            current_fcf: 当前自由现金流
            growth_rates: 现金流增长率，可以是单一数值或包含各年增长率的列表
            discount_rate: 贴现率
            terminal_growth_rate: 终值阶段增长率，默认为3%
            years: 预测年数，当growth_rates为单一数值时有效
            
        返回:
            估值价格
        """
        if current_fcf <= 0:
            raise ValueError("当前自由现金流必须为正数")
        if terminal_growth_rate >= discount_rate:
            raise ValueError("终值增长率必须小于贴现率")
        
        # 处理增长率，如果是单一数值则转换为列表
        if isinstance(growth_rates, float) or isinstance(growth_rates, int):
            growth_rates = [growth_rates] * years
        elif len(growth_rates) != years:
            raise ValueError(f"增长率列表长度必须为{years}")
        
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
        
        # 总估值
        enterprise_value = fcf_pv + terminal_value_pv
        
        self.results['DCF估值'] = {
            '当前自由现金流': current_fcf,
            '各年增长率': growth_rates,
            '贴现率': discount_rate,
            '终值增长率': terminal_growth_rate,
            '预测年数': years,
            '预测期现值': fcf_pv,
            '终值现值': terminal_value_pv,
            '企业价值': enterprise_value
        }
        
        return enterprise_value
    
    def get_summary(self, current_price: Optional[float] = None) -> pd.DataFrame:
        """
        获取所有估值结果的汇总
        
        参数:
            current_price: 当前市场价格，用于计算估值溢价/折价
            
        返回:
            包含所有估值结果的DataFrame
        """
        if not self.results:
            raise ValueError("尚未进行任何估值计算")
        
        summary_data = []
        for method, details in self.results.items():
            row = {
                '估值方法': method,
                '估值价格': details['估值价格'],
            }
            
            if current_price is not None:
                row['与市场价比率'] = details['估值价格'] / current_price
                row['溢价/折价'] = '溢价' if details['估值价格'] > current_price else '折价'
            
            summary_data.append(row)
        
        return pd.DataFrame(summary_data)


# 使用示例
if __name__ == "__main__":
    # 创建估值工具实例
    valuer = StockValuationTool()
    
    # 1. 市盈率估值
    try:
        pe_price = valuer.pe_valuation(
            earnings_per_share=5.2,    # 每股收益
            industry_pe=18.5,          # 行业平均市盈率
            company_risk_factor=0.95   # 公司风险因子
        )
        print(f"市盈率估值价格: {pe_price:.2f}元")
    except ValueError as e:
        print(f"市盈率估值出错: {e}")
    
    # 2. 市净率估值
    try:
        pb_price = valuer.pb_valuation(
            book_value_per_share=35.8, # 每股净资产
            industry_pb=2.4,           # 行业平均市净率
            roe=0.18,                  # 公司ROE
            industry_roe=0.15          # 行业平均ROE
        )
        print(f"市净率估值价格: {pb_price:.2f}元")
    except ValueError as e:
        print(f"市净率估值出错: {e}")
    
    # 3. 股利贴现模型估值
    try:
        ddm_price = valuer.ddm_valuation(
            current_dividend=2.1,      # 当前股息
            growth_rate=0.12,          # 股息增长率
            discount_rate=0.15,        # 贴现率
            high_growth_period=5,      # 高增长期5年
            stable_growth_rate=0.05    # 稳定增长率
        )
        print(f"股利贴现模型估值价格: {ddm_price:.2f}元")
    except ValueError as e:
        print(f"股利贴现模型估值出错: {e}")
    
    # 4. 现金流折现法估值
    try:
        # 假设公司前5年增长率逐渐下降
        growth_rates = [0.15, 0.14, 0.12, 0.10, 0.08]
        dcf_value = valuer.dcf_valuation(
            current_fcf=150000000,     # 当前自由现金流(单位:元)
            growth_rates=growth_rates, # 各年增长率
            discount_rate=0.14,        # 贴现率
            terminal_growth_rate=0.03, # 终值增长率
            years=5                    # 预测年数
        )
        print(f"现金流折现法企业价值: {dcf_value/100000000:.2f}亿元")
    except ValueError as e:
        print(f"现金流折现法估值出错: {e}")
    
    # 打印汇总结果
    print("\n估值结果汇总:")
    current_market_price = 95.0  # 当前市场价格
    summary = valuer.get_summary(current_price=current_market_price)
    print(summary.round(2))
