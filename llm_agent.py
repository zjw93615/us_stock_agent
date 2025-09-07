import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import openai
from tools import ToolManager, Tool
from logger import get_logger

# 获取日志记录器
logger = get_logger()

# 加载环境变量
load_dotenv()

class LLMStockAgent:
    def __init__(self, news_api_key: str, model_name: str = "gpt-4"):
        self.model_name = model_name
        self.tool_manager = ToolManager(news_api_key)
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",)
        
        # 系统提示词 - 定义Agent的角色和行为准则
        self.system_prompt = self._create_system_prompt()
        
        # 对话历史
        self.conversation_history = [{"role": "system", "content": self.system_prompt}]
    
    def _create_system_prompt(self) -> str:
        """创建系统提示词，定义Agent的行为方式"""
        tool_descriptions = self.tool_manager.get_all_tool_descriptions()
        
        # 获取当前系统日期
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        return f"""你是一个专业的股票分析AI助手，能够分析股票数据并提供投资见解。

今天的日期是: {current_date}

你可以使用以下工具来获取所需的数据：

{tool_descriptions}

你的工作流程：
1. 分析用户的问题，确定需要哪些数据
2. 选择合适的工具获取所需数据
3. 如果已有数据不足以回答问题，继续调用其他必要的工具
4. 基于所有获取的数据，提供全面、深入的分析

调用工具的格式：
当你需要调用工具时，请使用以下格式包裹内容：
<tool_call>
{{
  "name": "工具名称",
  "parameters": {{
    "参数1": "值1",
    "参数2": "值2"
  }}
}}
</tool_call>

注意事项：
- 只在需要获取数据时调用工具
- 确保提供工具所需的所有必要参数
- 调用工具后，根据返回结果决定是否需要进一步调用其他工具
- 最终分析应基于所有获取的数据，用自然语言清晰表达
- 分析应包括技术面分析、基本面分析和新闻情感分析（如适用）
- 明确说明分析的局限性和潜在风险
"""
    
    def _parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """解析大模型的响应，提取工具调用指令"""
        start_tag = "<tool_call>"
        end_tag = "</tool_call>"
        
        start_idx = response.find(start_tag)
        end_idx = response.find(end_tag)
        
        if start_idx == -1 or end_idx == -1:
            logger.debug("未在LLM响应中找到工具调用标记")
            return None
            
        try:
            tool_call_str = response[start_idx + len(start_tag):end_idx].strip()
            logger.debug(f"提取到工具调用文本: {tool_call_str[:100]}...")
            result = json.loads(tool_call_str)
            logger.debug(f"成功解析工具调用JSON: {result['name'] if 'name' in result else '未知工具'}")
            return result
        except json.JSONDecodeError:
            logger.error("解析工具调用JSON失败")
            return None
    
    def _run_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        tool_name = tool_call.get("name")
        parameters = tool_call.get("parameters", {})
        
        logger.info(f"准备执行工具: {tool_name}")
        logger.debug(f"工具参数: {json.dumps(parameters)}")
        
        if not tool_name:
            logger.warning("未指定工具名称")
            return {"error": "未指定工具名称"}
        
        tool = self.tool_manager.get_tool(tool_name)
        if not tool:
            logger.warning(f"未找到工具: {tool_name}")
            return {"error": f"未知工具: {tool_name}"}
        
        try:
            logger.info(f"开始执行工具: {tool_name}")
            result = tool.run(** parameters)
            logger.info(f"工具 {tool_name} 执行成功")
            return {
                "status": "success",
                "tool": tool_name,
                "parameters": parameters,
                "result": result
            }
        except Exception as e:
            logger.error(f"工具 {tool_name} 执行失败: {str(e)}")
            return {
                "status": "error",
                "tool": tool_name,
                "parameters": parameters,
                "error": str(e)
            }
    
    def analyze(self, user_query: str, max_steps: int = 5, step_callback=None) -> Dict[str, Any]:
        """处理用户查询，进行分析"""
        logger.info(f"开始分析用户查询: {user_query}")
        self.conversation_history.append({"role": "user", "content": user_query})
        
        steps = []
        final_analysis = None
        
        for step in range(max_steps):
            logger.info(f"执行分析步骤 {step+1}/{max_steps}")
            # 调用大模型获取响应
            logger.debug(f"向OpenAI发送请求，模型: {self.model_name}")
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=self.conversation_history
            )
            
            llm_response = response.choices[0].message.content
            logger.debug(f"收到OpenAI响应: {llm_response}")
            self.conversation_history.append({"role": "assistant", "content": llm_response})
            
            # 记录步骤
            step_data = {
                "step": step + 1,
                "llm_response": llm_response
            }
            steps.append(step_data)
            
            # 实时发送思考过程
            if step_callback:
                # 提取不包含工具调用标记的部分
                clean_response = llm_response
                tool_call_start = clean_response.find('<tool_call>')
                if tool_call_start != -1:
                    clean_response = clean_response[:tool_call_start].strip()
                
                if clean_response.strip():
                    step_callback({
                        "type": "thinking",
                        "content": f"💭 步骤 {step+1}: {clean_response}"
                    })
            
            # 检查是否包含工具调用
            tool_call = self._parse_tool_call(llm_response)
            
            if not tool_call:
                # 没有工具调用，说明分析完成
                logger.info("未检测到工具调用，分析完成")
                final_analysis = llm_response
                break
            
            # 执行工具调用
            logger.info(f"检测到工具调用: {tool_call['name'] if tool_call else 'None'}")
            
            # 实时发送工具调用信息
            if step_callback and tool_call:
                tool_name = tool_call.get("name", "未知工具")
                tool_params = tool_call.get("parameters", {})
                
                # 根据工具类型生成描述
                if tool_name == "get_historical_data":
                    ticker = tool_params.get("ticker", "")
                    step_callback({
                        "type": "tool",
                        "content": f"📊 正在获取 {ticker} 的历史数据..."
                    })
                elif tool_name == "get_financial_statements":
                    ticker = tool_params.get("ticker", "")
                    step_callback({
                        "type": "tool",
                        "content": f"📈 正在获取 {ticker} 的财务报表..."
                    })
                elif tool_name == "get_stock_news":
                    ticker = tool_params.get("ticker", "")
                    step_callback({
                        "type": "tool",
                        "content": f"📰 正在获取 {ticker} 的最新新闻..."
                    })
                elif tool_name == "calculate_technical_indicators":
                    ticker = tool_params.get("ticker", "")
                    step_callback({
                        "type": "tool",
                        "content": f"📉 正在计算 {ticker} 的技术指标..."
                    })
                else:
                    step_callback({
                        "type": "tool",
                        "content": f"🔧 正在调用工具: {tool_name}"
                    })
            
            tool_result = self._run_tool(tool_call)
            steps[-1]["tool_call"] = tool_call
            steps[-1]["tool_result"] = tool_result
            
            # 发送工具执行完成信息
            if step_callback:
                step_callback({
                    "type": "thinking",
                    "content": "✅ 工具执行完成，正在分析结果..."
                })
            
            # 将工具结果返回给大模型
            # 处理可能包含Timestamp类型键的字典
            def json_serializable(obj):
                import pandas as pd
                if isinstance(obj, dict):
                    return {str(k): json_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [json_serializable(i) for i in obj]
                elif isinstance(obj, pd.Timestamp):
                    return str(obj)
                else:
                    return obj
            
            serializable_result = json_serializable(tool_result)
            tool_result_msg = f"工具调用结果:\n{json.dumps(serializable_result, indent=2)}"
            logger.debug(f"工具调用结果: {json.dumps(serializable_result)}")
            self.conversation_history.append({"role": "user", "content": tool_result_msg})
        
        # 如果达到最大步数但还没有最终分析，请求一个总结
        if final_analysis is None:
            logger.info("达到最大步数限制，请求最终分析总结")
            summary_prompt = "请基于以上所有信息，提供一个完整的分析总结和投资建议。不要再调用任何工具。"
            self.conversation_history.append({"role": "user", "content": summary_prompt})
            
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=self.conversation_history
            )
            
            final_analysis = response.choices[0].message.content
            logger.info("生成最终分析总结完成")
            
            # 记录最终总结步骤
            steps.append({
                "step": len(steps) + 1,
                "llm_response": final_analysis,
                "is_final_summary": True
            })
        
        # 发送最终分析结果
        if step_callback and final_analysis:
            step_callback({
                "type": "final",
                "content": final_analysis
            })
        
        return {
            "query": user_query,
            "steps": steps,
            "final_analysis": final_analysis,
            "completed": final_analysis is not None
        }
