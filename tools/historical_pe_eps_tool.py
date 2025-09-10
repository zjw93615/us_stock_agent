# 获取历史PE和EPS获取工具
from tools.base_tool import Tool
from logger import get_logger

# 获取日志记录器
logger = get_logger()

class HistoricalPEEPSTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_historical_pe_eps",
            description="获取股票的历史PE比率和EPS数据，以及相关统计分析",
            parameters={
                "ticker": {"type": "str", "description": "股票代码，如AAPL"},
                "period": {"type": "str", "description": "分析周期，可选值：'1y', '5y', '10y'"}
            },
        )
        
    def run(self, ticker, period='1y'):
        logger.info(f"获取股票历史PE比率和EPS数据: 股票={ticker}, 周期={period}")
        import yfinance as yf
        import pandas as pd
        ticker = yf.Ticker(ticker)
        
        # 获取股价历史数据
        price_history = ticker.history(period=period)
        
        # 获取季度财务数据
        quarterly_earnings = ticker.quarterly_earnings
        
        # 如果没有季度数据，尝试获取年度数据
        if quarterly_earnings.empty:
            quarterly_earnings = ticker.earnings
        
        # 创建结果数据框
        pe_history = []
        
        # 对于每个财报日期
        for date, row in quarterly_earnings.iterrows():
            earnings = row['Earnings']
            if earnings <= 0:  # 跳过负EPS
                continue
                
            # 找到最接近的交易日
            closest_date = price_history.index[price_history.index >= date].min()
            if pd.isna(closest_date):
                continue
                
            price = price_history.loc[closest_date, 'Close']
            pe_ratio = price / (earnings / 4)  # 将季度收益年化
            
            pe_history.append({
                'Date': closest_date,
                'Price': price,
                'EPS (Quarterly)': earnings,
                'EPS (Annualized)': earnings * 4,
                'PE': pe_ratio
            })
            
        df = pd.DataFrame(pe_history)
        data = {
            "history_pe": pe_history,
            "PE avg": df['PE'].mean(),
            "PE high": df['PE'].max(),
            "PE low": df["PE"].min(),
            "PE median": df["PE"].median(),
        }
        
        return data