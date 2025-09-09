from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
from llm_agent import LLMStockAgent
from logger import get_logger

# 获取日志记录器
logger = get_logger()

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__)

# 读取应用配置
flask_env = os.getenv("FLASK_ENV", "development")
flask_debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
flask_port = int(os.getenv("FLASK_PORT", "5000"))
openai_model = os.getenv("OPENAI_MODEL", "qwen-flash")
news_api_key = os.getenv("NEWS_API_KEY")

# 配置Flask应用
app.config["ENV"] = flask_env
app.config["DEBUG"] = flask_debug

logger.info(f"Flask应用配置: ENV={flask_env}, DEBUG={flask_debug}, PORT={flask_port}")
logger.info(f"使用模型: {openai_model}")

# 创建Agent实例
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("请确保设置了OPENAI_API_KEY环境变量")
    raise ValueError("缺少OPENAI_API_KEY环境变量")

agent = LLMStockAgent(news_api_key=news_api_key, model_name=openai_model)


@app.route("/")
def index():
    """渲染主页"""
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """处理股票分析请求"""
    data = request.json
    user_query = data.get("query", "")

    if not user_query.strip():
        user_query = (
            "分析一下苹果公司(AAPL)最近三个月的股票表现，包括技术指标和相关新闻"
        )
        logger.info(f"使用默认查询: {user_query}")

    logger.info(f"查询: {user_query}")
    logger.info("正在分析，请稍候...")

    # 执行分析
    result = agent.analyze(user_query)

    # 返回结果
    return jsonify(result)


@app.route("/api/visualization", methods=["POST"])
def visualization():
    """生成股票数据可视化"""
    data = request.json
    ticker = data.get("ticker", "")
    query = data.get("query", "")
    start_date = data.get("start_date", "")
    end_date = data.get("end_date", "")
    chart_type = data.get("chart_type", "price")

    # 如果没有提供ticker，尝试从query中提取
    if not ticker and query:
        # 简单的股票代码提取逻辑
        import re

        # 查找常见的股票代码模式（大写字母，1-5个字符）
        stock_patterns = re.findall(r"\b[A-Z]{1,5}\b", query.upper())
        common_stocks = [
            "AAPL",
            "GOOGL",
            "MSFT",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
            "NFLX",
            "BABA",
            "JD",
        ]

        # 优先选择常见股票代码
        for pattern in stock_patterns:
            if pattern in common_stocks:
                ticker = pattern
                break

        # 如果没有找到常见股票，使用第一个匹配的模式
        if not ticker and stock_patterns:
            ticker = stock_patterns[0]

        # 如果还是没有找到，使用默认值
        if not ticker:
            ticker = "AAPL"

    # 确保ticker不为空
    if not ticker:
        ticker = "AAPL"

    try:
        # 获取股票历史数据
        from tools import HistoricalDataTool, TechnicalAnalysisTool
        import pandas as pd

        # 如果未提供日期，使用默认值（最近3个月）
        if not start_date or not end_date:
            from datetime import datetime, timedelta

            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

        # 根据图表类型获取不同的数据
        if chart_type == "technical":
            # 获取技术指标
            tech_tool = TechnicalAnalysisTool()
            result = tech_tool.run(ticker, start_date, end_date)

            # 转换数据格式以便前端绘图
            dates = list(result["SMA50"].keys())
            dates.sort()

            chart_data = {
                "labels": [str(date) for date in dates],
                "datasets": [
                    {
                        "label": "SMA50",
                        "data": [result["SMA50"].get(date) for date in dates],
                        "borderColor": "rgba(75, 192, 192, 1)",
                        "fill": False,
                    },
                    {
                        "label": "SMA200",
                        "data": [result["SMA200"].get(date) for date in dates],
                        "borderColor": "rgba(153, 102, 255, 1)",
                        "fill": False,
                    },
                    {
                        "label": "RSI",
                        "data": [result["RSI"].get(date) for date in dates],
                        "borderColor": "rgba(255, 159, 64, 1)",
                        "fill": False,
                    },
                ],
            }

            return jsonify(
                {
                    "status": "success",
                    "chart_type": "line",
                    "title": f"{ticker} 技术指标",
                    "data": chart_data,
                }
            )
        else:
            # 获取价格历史数据
            hist_tool = HistoricalDataTool()
            result = hist_tool.run(ticker, start_date, end_date)

            # 转换数据格式以便前端绘图
            # 将字典键（可能是Timestamp）转换为字符串
            def json_serializable(obj):
                if isinstance(obj, dict):
                    return {str(k): json_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [json_serializable(i) for i in obj]
                elif isinstance(obj, pd.Timestamp):
                    return str(obj)
                else:
                    return obj

            serializable_result = json_serializable(result)

            # 提取日期和价格数据
            dates = list(serializable_result["Close"].keys())
            dates.sort()

            chart_data = {
                "labels": dates,
                "datasets": [
                    {
                        "label": "收盘价",
                        "data": [
                            serializable_result["Close"].get(date) for date in dates
                        ],
                        "borderColor": "rgba(75, 192, 192, 1)",
                        "backgroundColor": "rgba(75, 192, 192, 0.2)",
                        "fill": True,
                    },
                    {
                        "label": "交易量",
                        "data": [
                            serializable_result["Volume"].get(date) for date in dates
                        ],
                        "type": "bar",
                        "backgroundColor": "rgba(153, 102, 255, 0.5)",
                        "yAxisID": "volume",
                    },
                ],
            }

            return jsonify(
                {
                    "status": "success",
                    "chart_type": "mixed",
                    "title": f"{ticker} 价格历史",
                    "data": chart_data,
                }
            )
    except Exception as e:
        logger.error(f"生成可视化数据失败: {str(e)}")
        return jsonify({"status": "error", "message": f"生成可视化数据失败: {str(e)}"})


@app.route("/api/stream", methods=["POST"])
def stream():
    """流式返回分析结果，用于实时显示思考过程"""
    from flask import Response
    import time
    import json

    data = request.json
    user_query = data.get("query", "")

    if not user_query.strip():
        return jsonify({"error": "查询不能为空"})

    def generate():
        """生成流式响应"""
        import queue
        import threading

        # 创建一个队列来在线程间传递数据
        data_queue = queue.Queue()

        # 发送初始消息
        yield json.dumps(
            {"type": "thinking", "content": "🤔 正在分析您的查询..."}
        ) + "\n"

        try:
            # 创建回调函数来实时发送数据
            def step_callback(data):
                data_queue.put(json.dumps(data) + "\n")

            # 在单独线程中执行分析
            def run_analysis():
                try:
                    stream_agent = LLMStockAgent(
                        news_api_key=None, model_name="qwen-flash"
                    )
                    result = stream_agent.analyze(
                        user_query, max_steps=10, step_callback=step_callback
                    )
                    # 分析完成，发送结束信号
                    data_queue.put(None)
                except Exception as e:
                    # 发送错误信息
                    data_queue.put(
                        json.dumps(
                            {
                                "type": "error",
                                "content": f"分析过程中出现错误: {str(e)}",
                            }
                        )
                        + "\n"
                    )
                    data_queue.put(None)

            # 启动分析线程
            analysis_thread = threading.Thread(target=run_analysis)
            analysis_thread.start()

            # 持续从队列中获取数据并发送
            while True:
                try:
                    data = data_queue.get(timeout=300)  # 300秒超时
                    if data is None:  # 结束信号
                        break
                    yield data
                except queue.Empty:
                    # 超时，发送错误信息
                    yield json.dumps(
                        {"type": "error", "content": "分析超时，请重试"}
                    ) + "\n"
                    break

            # 等待分析线程完成
            analysis_thread.join(timeout=5)
        except Exception as e:
            logger.error(f"流式分析出错: {str(e)}")
            yield json.dumps(
                {"type": "error", "content": f"分析过程中出现错误: {str(e)}"}
            ) + "\n"

    # 返回流式响应
    return Response(generate(), mimetype="application/x-ndjson")


if __name__ == "__main__":
    logger.info(f"启动Flask应用，监听端口: {flask_port}")
    app.run(debug=flask_debug, port=flask_port, host="0.0.0.0")
