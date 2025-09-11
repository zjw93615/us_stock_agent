import os
import json
import re
import time
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
from logger import get_logger

from tool_manager import Tool

logger = get_logger()


class WebSearchAndAnalysisTool(object):
    """
    网络搜索和信息整理工具
    类似DeepSeek或豆包的网络搜索功能，能够搜索、整理和分析网络信息
    """
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        self.SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
        
        # 配置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def search_and_analyze(self, query: str, search_type: str = "general", 
                          max_results: int = 10, analysis_focus: str = "general") -> Dict[str, Any]:
        """
        主要搜索和分析函数
        
        Args:
            query: 搜索查询关键词
            search_type: 搜索类型 - 'general', 'news', 'finance', 'company', 'academic'
            max_results: 最大结果数量
            analysis_focus: 分析重点 - 'investment_risk', 'market_trend', 'company_analysis', 'general'
        
        Returns:
            结构化的搜索和分析结果
        """
        logger.info(f"开始网络搜索和分析: query='{query}', type={search_type}, focus={analysis_focus}")
        
        try:
            # 第一步：执行多渠道搜索
            search_results = self._perform_comprehensive_search(query, search_type, max_results)
            
            if not search_results:
                return {
                    "status": "error",
                    "message": "未找到相关搜索结果",
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 第二步：内容提取和预处理
            extracted_content = self._extract_and_clean_content(search_results)
            
            # 第三步：AI智能分析
            analysis_result = self._ai_intelligent_analysis(extracted_content, query, analysis_focus)
            
            # 第四步：结构化输出
            final_result = self._build_final_result(
                query, search_type, analysis_focus, search_results, analysis_result
            )
            
            logger.info(f"搜索和分析完成: 处理了{len(search_results)}个结果")
            return final_result
            
        except Exception as e:
            logger.error(f"搜索和分析过程失败: {str(e)}")
            return {
                "status": "error",
                "message": f"搜索和分析过程出现错误: {str(e)}",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
    
    def _perform_comprehensive_search(self, query: str, search_type: str, max_results: int) -> List[Dict]:
        """执行综合搜索，结合多个搜索引擎和数据源"""
        all_results = []
        
        # 1. DuckDuckGo搜索（主要搜索源）
        try:
            ddg_results = self._duckduckgo_search(query, max_results // 2)
            all_results.extend(ddg_results)
            logger.info(f"DuckDuckGo搜索获得{len(ddg_results)}个结果")
        except Exception as e:
            logger.warning(f"DuckDuckGo搜索失败: {str(e)}")
        
        # 2. Google免费搜索（使用googlesearch-python库）
        # if len(all_results) < max_results:
        #     try:
        #         google_results = self._google_custom_search(query, max_results - len(all_results))
        #         all_results.extend(google_results)
        #         logger.info(f"Google搜索获得{len(google_results)}个结果")
        #     except Exception as e:
        #         logger.warning(f"Google搜索失败: {str(e)}")
        
        # 3. SerpAPI搜索（如果配置了API）
        if self.SERPAPI_API_KEY and len(all_results) < max_results:
            try:
                serp_results = self._serpapi_search(query, max_results - len(all_results))
                all_results.extend(serp_results)
                logger.info(f"SerpAPI搜索获得{len(serp_results)}个结果")
            except Exception as e:
                logger.warning(f"SerpAPI搜索失败: {str(e)}")
        
        # 4. 特定类型的增强搜索
        if search_type == "finance":
            finance_results = self._finance_enhanced_search(query)
            all_results.extend(finance_results)
        elif search_type == "news":
            news_results = self._news_enhanced_search(query)
            all_results.extend(news_results)
        elif search_type == "company":
            company_results = self._company_enhanced_search(query)
            all_results.extend(company_results)
        elif search_type == "academic":
            academic_results = self._academic_enhanced_search(query)
            all_results.extend(academic_results)
        
        # 去重、排序和筛选
        unique_results = self._deduplicate_and_rank_results(all_results)
        return unique_results[:max_results]
    
    def _duckduckgo_search(self, query: str, max_results: int) -> List[Dict]:
        """使用DuckDuckGo搜索"""
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                search_results = ddgs.text(query, max_results=max_results)
                for result in search_results:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                        "source": "DuckDuckGo",
                        "relevance_score": 0.8  # 基础相关性分数
                    })
            return results
        except ImportError:
            logger.warning("duckduckgo-search库未安装，跳过DuckDuckGo搜索")
            return []
        except Exception as e:
            logger.warning(f"DuckDuckGo搜索出错: {str(e)}")
            return []
    
    def _google_custom_search(self, query: str, max_results: int) -> List[Dict]:
        """使用googlesearch-python库进行免费Google搜索"""
        try:
            from googlesearch import search
            import time
            
            results = []
            search_results = []
            
            # 使用googlesearch-python获取搜索结果
            # 限制搜索数量避免被限制，并添加延迟
            for url in search(query, num_results=min(max_results, 10), lang='en', pause=2):
                search_results.append(url)
                if len(search_results) >= max_results:
                    break
            
            # 获取每个URL的标题和摘要
            for i, url in enumerate(search_results):
                try:
                    # 获取网页标题和摘要
                    response = requests.get(url, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # 获取标题
                        title_tag = soup.find('title')
                        title = title_tag.get_text().strip() if title_tag else f"搜索结果 {i+1}"
                        
                        # 获取描述（尝试多个meta标签）
                        description = ""
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        if not meta_desc:
                            meta_desc = soup.find('meta', attrs={'property': 'og:description'})
                        if meta_desc:
                            description = meta_desc.get('content', '')
                        
                        # 如果没有描述，从正文提取前200个字符
                        if not description:
                            text_content = soup.get_text()
                            # 清理文本
                            lines = (line.strip() for line in text_content.splitlines())
                            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                            clean_text = ' '.join(chunk for chunk in chunks if chunk)
                            description = clean_text[:200] + "..." if len(clean_text) > 200 else clean_text
                        
                        results.append({
                            "title": title[:100] + "..." if len(title) > 100 else title,
                            "url": url,
                            "snippet": description[:300] + "..." if len(description) > 300 else description,
                            "source": "Google",
                            "relevance_score": 0.9
                        })
                    else:
                        # 如果无法获取网页内容，仍然添加基础信息
                        results.append({
                            "title": f"Google搜索结果 {i+1}",
                            "url": url,
                            "snippet": "无法获取网页摘要",
                            "source": "Google",
                            "relevance_score": 0.8
                        })
                    
                    # 添加延迟避免请求过快
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"获取网页信息失败 {url}: {str(e)}")
                    # 即使获取详细信息失败，也保留URL
                    results.append({
                        "title": f"Google搜索结果 {i+1}",
                        "url": url,
                        "snippet": "网页信息获取失败",
                        "source": "Google",
                        "relevance_score": 0.7
                    })
            
            logger.info(f"Google搜索完成，获得{len(results)}个结果")
            return results
            
        except ImportError:
            logger.warning("googlesearch-python库未安装，跳过Google搜索")
            return []
        except Exception as e:
            logger.warning(f"Google搜索失败: {str(e)}")
            return []
    
    def _serpapi_search(self, query: str, max_results: int) -> List[Dict]:
        """使用SerpAPI搜索"""
        try:
            import serpapi
            
            client = serpapi.Client(api_key=self.SERPAPI_API_KEY)
            results_data = client.search({
                'engine': 'google',
                'q': query,
                'num': min(max_results, 10)
            })
            
            results = []
            
            for result in results_data.get("organic_results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "source": "SerpAPI",
                    "relevance_score": 0.85
                })
            
            return results
        except ImportError:
            logger.warning("serpapi库未安装，跳过SerpAPI搜索")
            return []
        except Exception as e:
            logger.warning(f"SerpAPI搜索失败: {str(e)}")
            return []
    
    def _finance_enhanced_search(self, query: str) -> List[Dict]:
        """财经专门搜索"""
        finance_sites = [
            "site:bloomberg.com",
            "site:reuters.com", 
            "site:cnbc.com",
            "site:marketwatch.com",
            "site:yahoo.com/finance",
            "site:wsj.com",
            "site:ft.com"
        ]
        
        results = []
        for site in finance_sites[:3]:  # 限制查询数量
            enhanced_query = f"{query} {site}"
            try:
                site_results = self._duckduckgo_search(enhanced_query, 2)
                for result in site_results:
                    result["relevance_score"] = 0.95  # 财经网站相关性更高
                results.extend(site_results)
                time.sleep(0.5)  # 避免请求过快
            except:
                continue
        
        return results
    
    def _news_enhanced_search(self, query: str) -> List[Dict]:
        """新闻专门搜索"""
        # 搜索最近的新闻
        recent_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        news_queries = [
            f"{query} news",
            f"{query} latest news",
            f"{query} breaking news",
            f'"{query}" after:{recent_date}'
        ]
        
        results = []
        for news_query in news_queries[:2]:
            try:
                news_results = self._duckduckgo_search(news_query, 3)
                for result in news_results:
                    result["relevance_score"] = 0.9
                results.extend(news_results)
                time.sleep(0.5)
            except:
                continue
        
        return results
    
    def _company_enhanced_search(self, query: str) -> List[Dict]:
        """公司信息专门搜索"""
        company_queries = [
            f"{query} company profile",
            f"{query} investor relations",
            f"{query} annual report",
            f"{query} SEC filing",
            f'site:sec.gov "{query}"'
        ]
        
        results = []
        for comp_query in company_queries[:3]:
            try:
                comp_results = self._duckduckgo_search(comp_query, 2)
                for result in comp_results:
                    result["relevance_score"] = 0.92
                results.extend(comp_results)
                time.sleep(0.5)
            except:
                continue
        
        return results
    
    def _academic_enhanced_search(self, query: str) -> List[Dict]:
        """学术研究专门搜索"""
        academic_sites = [
            "site:scholar.google.com",
            "site:arxiv.org",
            "site:ssrn.com",
            "site:jstor.org"
        ]
        
        results = []
        for site in academic_sites[:2]:
            enhanced_query = f"{query} {site}"
            try:
                academic_results = self._duckduckgo_search(enhanced_query, 2)
                for result in academic_results:
                    result["relevance_score"] = 0.88
                results.extend(academic_results)
                time.sleep(0.5)
            except:
                continue
        
        return results
    
    def _deduplicate_and_rank_results(self, results: List[Dict]) -> List[Dict]:
        """去重并按相关性排序搜索结果"""
        # 去重（基于URL）
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get("url", "").lower()
            # 清理URL以更好地去重
            clean_url = url.split('?')[0].split('#')[0]
            
            if clean_url and clean_url not in seen_urls:
                seen_urls.add(clean_url)
                unique_results.append(result)
        
        # 按相关性分数排序
        unique_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return unique_results
    
    def _extract_and_clean_content(self, search_results: List[Dict]) -> str:
        """从搜索结果中提取和清洗内容"""
        from bs4 import BeautifulSoup
        
        extracted_contents = []
        
        for i, result in enumerate(search_results[:8]):  # 处理前8个结果
            try:
                content_piece = f"=== 来源 {i+1}: {result['title']} ===\n"
                content_piece += f"URL: {result['url']}\n"
                content_piece += f"摘要: {result['snippet']}\n"
                
                # 对前3个高质量结果获取完整网页内容
                if i < 3 and result.get("relevance_score", 0) > 0.85:
                    try:
                        logger.info(f"正在提取网页内容: {result['url']}")
                        response = requests.get(
                            result['url'], 
                            headers=self.headers, 
                            timeout=15,
                            allow_redirects=True
                        )
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            
                            # 移除不需要的元素
                            for element in soup(["script", "style", "nav", "footer", "aside", "iframe"]):
                                element.decompose()
                            
                            # 提取主要内容
                            main_content = ""
                            
                            # 尝试提取主要内容区域
                            content_selectors = [
                                'article', 'main', '.content', '.post-content', 
                                '.article-body', '.story-body', '#content'
                            ]
                            
                            for selector in content_selectors:
                                content_elem = soup.select_one(selector)
                                if content_elem:
                                    main_content = content_elem.get_text()
                                    break
                            
                            # 如果没找到特定区域，使用body内容
                            if not main_content:
                                body = soup.find('body')
                                if body:
                                    main_content = body.get_text()
                            
                            # 清理文本
                            if main_content:
                                lines = (line.strip() for line in main_content.splitlines())
                                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                                clean_text = ' '.join(chunk for chunk in chunks if chunk)
                                
                                # 限制长度并截取有意义的部分
                                if len(clean_text) > 3000:
                                    clean_text = clean_text[:3000] + "..."
                                
                                content_piece += f"详细内容: {clean_text}\n"
                    
                    except Exception as e:
                        logger.warning(f"提取网页内容失败 {result['url']}: {str(e)}")
                        # 如果提取失败，仍然使用摘要内容
                
                content_piece += "\n" + "="*50 + "\n"
                extracted_contents.append(content_piece)
                
            except Exception as e:
                logger.warning(f"处理搜索结果时出错: {str(e)}")
        
        return "\n".join(extracted_contents)
    
    def _ai_intelligent_analysis(self, content: str, query: str, analysis_focus: str) -> Dict[str, Any]:
        """使用AI进行智能分析和总结"""
        if not self.openai_api_key:
            logger.warning("未配置OpenAI API密钥，返回基础分析")
            return self._basic_text_analysis(content, query)
        
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=self.openai_api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            # 构建智能分析提示词
            analysis_prompt = self._build_intelligent_prompt(query, analysis_focus, content)
            
            # 调用AI进行分析
            response = client.chat.completions.create(
                model="qwen-plus",  # 使用更强的模型进行分析
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一个专业的信息分析专家，擅长从大量网络信息中提取关键洞察，进行深度分析和总结。你的分析应该准确、全面、有深度，并能为决策提供有价值的参考。"
                    },
                    {"role": "user", "content": analysis_prompt}
                ],
                # temperature=0.3,
                # max_tokens=2000
            )
            
            analysis_text = response.choices[0].message.content
            logger.info("AI分析完成")
            
            # 解析和结构化分析结果
            return self._parse_ai_analysis_result(analysis_text)
            
        except Exception as e:
            logger.error(f"AI智能分析失败: {str(e)}")
            return self._basic_text_analysis(content, query)
    
    def _build_intelligent_prompt(self, query: str, analysis_focus: str, content: str) -> str:
        """构建智能分析提示词"""
        base_prompt = f"""
请对以下网络搜索结果进行深度分析，针对查询"{query}"提供专业见解。

分析重点: {analysis_focus}

网络搜索内容:
{content[:8000]}  # 限制内容长度避免超过token限制

请提供结构化的深度分析，包括：

1. **核心摘要** (Executive Summary): 用3-4句话概括最重要的信息和结论
2. **关键发现** (Key Findings): 列出5-7个最重要的发现、趋势或洞察
3. **数据要点** (Critical Data): 提取所有重要的数字、日期、百分比、统计数据
4. **风险与机会** (Risks & Opportunities): 识别潜在风险和投资/商业机会
5. **市场影响** (Market Impact): 分析对市场、行业或相关领域的影响
6. **可信度评估** (Credibility Assessment): 基于信息源的权威性和数据质量评估可信度(0-1)
7. **行动建议** (Action Items): 基于分析结果提出3-5个具体建议

请用JSON格式回复:
{{
    "executive_summary": "核心摘要...",
    "key_findings": [
        "发现1: 具体描述...",
        "发现2: 具体描述...",
        "发现3: 具体描述..."
    ],
    "critical_data": {{
        "关键指标名称": "具体数值和说明",
        "重要日期": "日期和事件描述"
    }},
    "risks_opportunities": {{
        "risks": ["风险1", "风险2"],
        "opportunities": ["机会1", "机会2"]
    }},
    "market_impact": {{
        "short_term": "短期影响描述",
        "long_term": "长期影响描述",
        "affected_sectors": ["受影响行业1", "受影响行业2"]
    }},
    "credibility_score": 0.85,
    "action_items": [
        "建议1: 具体行动...",
        "建议2: 具体行动..."
    ],
    "analysis_confidence": "high/medium/low",
    "additional_notes": "补充说明..."
}}
"""
        
        # 根据分析重点定制提示词
        if analysis_focus == "investment_risk":
            base_prompt += "\n**特别关注**: 投资风险评估、市场波动性、财务健康度、监管风险等。"
        elif analysis_focus == "market_trend":
            base_prompt += "\n**特别关注**: 市场趋势分析、价格走势、供需关系、行业动态等。"
        elif analysis_focus == "company_analysis":
            base_prompt += "\n**特别关注**: 公司基本面、财务表现、竞争地位、管理层变动、业务战略等。"
        elif analysis_focus == "technology_trend":
            base_prompt += "\n**特别关注**: 技术发展趋势、创新突破、专利情况、技术应用前景等。"
        
        return base_prompt
    
    def _parse_ai_analysis_result(self, analysis_text: str) -> Dict[str, Any]:
        """解析AI分析结果"""
        try:
            import re
            
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                # 验证必要字段
                required_fields = ["executive_summary", "key_findings", "credibility_score"]
                for field in required_fields:
                    if field not in result:
                        result[field] = f"未提供{field}"
                
                return result
        except Exception as e:
            logger.warning(f"JSON解析失败，使用文本解析: {str(e)}")
        
        # 备用文本解析
        return self._fallback_text_parsing(analysis_text)
    
    def _fallback_text_parsing(self, text: str) -> Dict[str, Any]:
        """备用文本解析方法"""
        lines = text.split('\n')
        
        result = {
            "executive_summary": "",
            "key_findings": [],
            "critical_data": {},
            "risks_opportunities": {"risks": [], "opportunities": []},
            "market_impact": {"short_term": "", "long_term": "", "affected_sectors": []},
            "credibility_score": 0.7,
            "action_items": [],
            "analysis_confidence": "medium"
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 识别章节
            if any(keyword in line.lower() for keyword in ["summary", "摘要"]):
                current_section = "summary"
            elif any(keyword in line.lower() for keyword in ["finding", "发现", "洞察"]):
                current_section = "findings"
            elif any(keyword in line.lower() for keyword in ["risk", "风险"]):
                current_section = "risks"
            elif any(keyword in line.lower() for keyword in ["opportunity", "机会"]):
                current_section = "opportunities"
            elif line.startswith(('-', '•', '*')) or re.match(r'^\d+\.', line):
                # 处理列表项
                clean_line = re.sub(r'^[-•*\d.)\s]+', '', line).strip()
                if current_section == "findings":
                    result["key_findings"].append(clean_line)
                elif current_section == "risks":
                    result["risks_opportunities"]["risks"].append(clean_line)
                elif current_section == "opportunities":
                    result["risks_opportunities"]["opportunities"].append(clean_line)
            elif current_section == "summary" and len(line) > 10:
                result["executive_summary"] += line + " "
        
        return result
    
    def _basic_text_analysis(self, content: str, query: str) -> Dict[str, Any]:
        """基础文本分析（无AI时的备用方案）"""
        # 简单的关键词提取和统计
        words = content.lower().split()
        word_freq = {}
        
        # 过滤停用词
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had'}
        
        for word in words:
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 提取高频词作为关键发现
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "executive_summary": f"基于网络搜索结果的基础分析，查询关键词: {query}",
            "key_findings": [f"高频关键词: {word} (出现{freq}次)" for word, freq in top_words[:5]],
            "critical_data": {"总字数": len(words), "唯一词汇数": len(word_freq)},
            "credibility_score": 0.6,
            "analysis_confidence": "low"
        }
    
    def _build_final_result(self, query: str, search_type: str, analysis_focus: str, 
                           search_results: List[Dict], analysis_result: Dict) -> Dict[str, Any]:
        """构建最终的结构化结果"""
        return {
            "status": "success",
            "query": query,
            "search_metadata": {
                "search_type": search_type,
                "analysis_focus": analysis_focus,
                "total_sources": len(search_results),
                "search_timestamp": datetime.now().isoformat(),
                "processing_time": "完成"
            },
            
            # AI分析结果
            "analysis": {
                "executive_summary": analysis_result.get("executive_summary", ""),
                "key_findings": analysis_result.get("key_findings", []),
                "critical_data": analysis_result.get("critical_data", {}),
                "risks_opportunities": analysis_result.get("risks_opportunities", {}),
                "market_impact": analysis_result.get("market_impact", {}),
                "action_items": analysis_result.get("action_items", []),
                "credibility_score": analysis_result.get("credibility_score", 0.7),
                "confidence_level": analysis_result.get("analysis_confidence", "medium")
            },
            
            # 搜索来源信息
            "sources": [
                {
                    "title": result["title"],
                    "url": result["url"],
                    "snippet": result["snippet"][:300] + "..." if len(result["snippet"]) > 300 else result["snippet"],
                    "source_engine": result.get("source", "Unknown"),
                    "relevance_score": result.get("relevance_score", 0.5)
                }
                for result in search_results[:8]  # 返回前8个源
            ],
            
            # 质量指标
            "quality_metrics": {
                "source_diversity": len(set(r.get("source", "unknown") for r in search_results)),
                "avg_relevance": sum(r.get("relevance_score", 0) for r in search_results) / len(search_results) if search_results else 0,
                "high_quality_sources": len([r for r in search_results if r.get("relevance_score", 0) > 0.8]),
                "analysis_completeness": "high" if len(analysis_result.get("key_findings", [])) >= 3 else "medium"
            }
        }


# 在tools.py中的集成工具类
class WebSearchIntegrationTool(Tool):
    """
    集成到现有工具系统中的Web搜索工具
    """
    def __init__(self):
        super().__init__(
            name="search_web_info",
            description="搜索网络信息并进行AI总结分析",
            parameters={
                "query": {"type": "str", "description": "搜索查询关键词"},
                "search_type": {"type": "str", "description": "搜索类型（可省略，默认general）：'general', 'news', 'finance', 'company', 'academic'"},
                "max_results": {"type": "int", "description": "最大结果数量（可省略，默认10）"},
                "analysis_focus": {"type": "str", "description": "分析重点（可省略，默认general）：'investment_risk', 'market_trend', 'company_analysis', 'general'等"}
            }
        )
    
    def run(self, query: str, search_type: str = "general", max_results: int = 10, analysis_focus: str = "general") -> Dict:
        """执行搜索和分析"""
        logger.info(f"执行网络搜索工具: query='{query}', type={search_type}")
        # 初始化搜索工具
        # self.search_tool = WebSearchAndAnalysisTool()
        try:
            result = WebSearchAndAnalysisTool().search_and_analyze(
                query=query,
                search_type=search_type,
                max_results=max_results,
                analysis_focus=analysis_focus
            )
            return result
        except Exception as e:
            logger.error(f"网络搜索工具执行失败: {str(e)}")
            raise


# 使用示例
if __name__ == "__main__":
    # 创建搜索工具实例
    search_tool = WebSearchAndAnalysisTool()
    
    # 示例搜索查询
    test_queries = [
        {
            "query": "Tesla Q3 2024 earnings report",
            "search_type": "finance",
            "analysis_focus": "investment_risk"
        },
        # {
        #     "query": "artificial intelligence stock market impact 2024",
        #     "search_type": "general", 
        #     "analysis_focus": "market_trend"
        # },
        # {
        #     "query": "Apple iPhone 15 sales performance",
        #     "search_type": "company",
        #     "analysis_focus": "company_analysis"
        # }
    ]
    
    for test_query in test_queries:
        print(f"\n{'='*60}")
        print(f"测试查询: {test_query['query']}")
        print(f"{'='*60}")
        
        result = search_tool.search_and_analyze(**test_query)
        
        if result["status"] == "success":
            print(f"执行摘要: {result['analysis']['executive_summary']}")
            print(f"\n关键发现:")
            for i, finding in enumerate(result['analysis']['key_findings'], 1):
                print(f"{i}. {finding}")
            
            print(f"\n可信度评分: {result['analysis']['credibility_score']:.2f}")
            print(f"信息源数量: {result['search_metadata']['total_sources']}")
        else:
            print(f"搜索失败: {result['message']}")