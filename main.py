import os
from dotenv import load_dotenv
from llm_agent import LLMStockAgent
from logger import get_logger

# 获取日志记录器
logger = get_logger()

# 加载环境变量
load_dotenv()

def main():
    # 从环境变量获取API密钥
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        logger.error("请确保设置了OPENAI_API_KEY环境变量")
        return
    
    # 创建Agent实例 - GNews不需要API密钥
    agent = LLMStockAgent(news_api_key=None, model_name="qwen-flash")
    
    # 获取用户输入的查询
    logger.info("请输入您的股票分析查询（例如：分析一下苹果公司(AAPL)最近三个月的股票表现）：")
    print("请输入您的股票分析查询（例如：分析一下苹果公司(AAPL)最近三个月的股票表现）：")  # 保留控制台提示
    user_query = input("> ")
    
    # 如果用户没有输入任何内容，使用默认查询
    if not user_query.strip():
        user_query = "分析一下苹果公司(AAPL)最近三个月的股票表现，包括技术指标和相关新闻"
        logger.info(f"使用默认查询: {user_query}")
        print(f"使用默认查询: {user_query}")  # 保留控制台提示
    
    logger.info(f"查询: {user_query}")
    
    # 执行分析
    logger.info("正在分析，请稍候...")
    print("正在分析，请稍候...\n")  # 保留控制台提示
    result = agent.analyze(user_query)
    
    # 输出结果
    logger.info("分析步骤:")
    print("分析步骤:")  # 保留控制台提示
    for step in result["steps"]:
        step_info = f"步骤 {step['step']}:"
        logger.info(step_info)
        print(f"\n{step_info}")
        
        llm_response_full = f"LLM思考: {step['llm_response']}"
        logger.info(llm_response_full)
        # 控制台输出仍保留预览以提高可读性
        llm_response_preview = f"LLM思考: {step['llm_response'][:200]}..."  # 只显示前200个字符
        print(llm_response_preview)
        
        if "tool_call" in step:
            tool_call_info = f"调用工具: {step['tool_call']['name']}"
            logger.info(tool_call_info)
            print(tool_call_info)
    
    logger.info("最终分析报告:")
    print("\n\n最终分析报告:")
    
    # 记录完整的分析报告到日志文件
    if result["final_analysis"]:
        logger.info("分析报告内容: %s", result["final_analysis"])
    else:
        logger.warning("未生成分析报告")
    
    # 控制台输出分析报告
    print(result["final_analysis"])

if __name__ == "__main__":
    main()

