# 新闻获取工具
from tools.base_tool import Tool
from typing import List, Dict
from logger import get_logger

# 获取日志记录器
logger = get_logger()

class NewsTool(Tool):
    def __init__(self, api_key: str = None):
        # GNews不需要API密钥，但保留参数以兼容现有代码
        super().__init__(
            name="get_news",
            description="获取相关的新闻 articles",
            parameters={
                "query": {
                    "type": "str",
                    "description": "搜索关键词，通常是股票相关的新闻或是希望查询的新闻内容",
                },
                "period": {"type": "str", "description": "时间周期，例如'7d'表示7天内的新闻"},
                # "from_date": {"type": "str", "description": "开始日期，格式YYYY-MM-DD"},
                # "to_date": {"type": "str", "description": "结束日期，格式YYYY-MM-DD"},
            },
        )

    def run(self, query: str, period: str) -> List[Dict]:
        logger.info(f"获取新闻: 查询={query}, 时间周期={period}")
        from gnews import GNews

        try:
            # 创建GNews实例
            google_news = GNews()
            logger.debug("成功创建GNews实例")

            # 设置语言和国家/地区
            google_news.language = "en"
            google_news.country = "US"  # 美国新闻源
            google_news.period = period or "7d"  # 默认为7天内的新闻
            google_news.max_results = 20  # number of responses across a keyword
            # if(from_date and to_date):
            #     from datetime import datetime
            #     from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
            #     to_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
            #     google_news.start_date = (from_date_obj.year, from_date_obj.month, from_date_obj.day)
            #     google_news.end_date = (to_date_obj.year, to_date_obj.month, to_date_obj.day)
            # else:
            #     google_news.period = '7d'  # 默认为7天内的新闻
            logger.debug(
                f"GNews配置: 语言={google_news.language}, 国家={google_news.country}, 时间段={google_news.period}"
            )

            # 获取新闻
            logger.info(f"开始获取关于 '{query}' 的新闻")
            news_results = google_news.get_news(query)
            logger.info(f"成功获取新闻，数量: {len(news_results)}")

            # 转换结果格式以匹配原来的API返回格式
            articles = []
            for item in news_results:
                article = {
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "url": item.get("url", ""),
                    "publishedAt": item.get("published date", ""),
                    "source": {"name": item.get("publisher", {}).get("title", "")},
                }
                articles.append(article)
                # 记录每篇文章的详细信息
                logger.debug(f"文章信息: {article}")

            logger.debug(f"新闻格式转换完成，返回{len(articles)}条新闻")
            return articles
        except Exception as e:
            logger.error(f"获取新闻失败: {str(e)}")
            raise