import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import openai
from tools import ToolManager
from logger import get_logger

# 获取日志记录器
logger = get_logger()

# 加载环境变量
load_dotenv()


class LLMStockAgent:
    def __init__(self, news_api_key: str, model_name: str = "gpt-4"):
        self.model_name = model_name
        self.tool_manager = ToolManager(news_api_key)
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

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

        return f"""你是一个专业的股票分析AI助手，专注于基于真实数据的客观分析。

今天的日期是: {current_date}

**核心原则：**
1. 只基于工具返回的真实数据进行分析，绝不编造数据
2. 明确区分事实和推测，避免过度解读
3. 承认数据局限性，不做绝对预测
4. 提供风险提示和免责声明

**可用工具：**
{tool_descriptions}

**分析框架：**
1. **数据收集阶段**：
   - 明确用户需求，确定所需数据类型
   - 系统性收集相关数据（价格、财务、技术指标、新闻）
   - 验证数据完整性和时效性

2. **客观分析阶段**：
   - 技术面：基于指标数值进行趋势判断
   - 基本面：基于财务数据评估公司健康度
   - 市场情绪：基于新闻内容分析市场预期
   - 风险评估：识别潜在风险因素

3. **结论表述**：
   - 明确标注数据来源和时间
   - 区分"数据显示"和"可能意味着"
   - 提供多种情景分析
   - 强调投资风险和不确定性

**工具调用格式：**
<tool_call>
{{
  "name": "工具名称",
  "parameters": {{
    "参数1": "值1",
    "参数2": "值2"
  }}
}}
</tool_call>

**严格要求：**
- 禁止编造任何数据或指标值
- 如果工具返回错误或空数据，必须如实说明
- 不得对股价做出具体的涨跌预测
- 必须在分析结尾包含风险提示
- 承认分析的局限性和时效性

**标准结尾模板：**
"以上分析基于{{数据时间}}的公开数据，仅供参考。股市投资存在风险，过往表现不代表未来结果。投资者应结合自身情况谨慎决策，必要时咨询专业投资顾问。"
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
            tool_call_str = response[start_idx + len(start_tag) : end_idx].strip()
            logger.debug(f"提取到工具调用文本: {tool_call_str[:100]}...")
            result = json.loads(tool_call_str)
            logger.debug(
                f"成功解析工具调用JSON: {result['name'] if 'name' in result else '未知工具'}"
            )
            return result
        except json.JSONDecodeError:
            logger.error("解析工具调用JSON失败")
            return None

    def _run_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用并验证数据质量"""
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
            result = tool.run(**parameters)

            # 数据验证和质量检查
            validated_result = self._validate_tool_result(tool_name, result, parameters)
            return validated_result
        except Exception as e:
            logger.error(f"工具 {tool_name} 执行失败: {str(e)}")
            return {
                "status": "error",
                "tool": tool_name,
                "parameters": parameters,
                "error": str(e),
                "data_quality": "error",
            }

    def _validate_tool_result(
        self, tool_name: str, result: Any, parameters: Dict
    ) -> Dict[str, Any]:
        """验证工具返回结果的质量和完整性"""
        validation_info = {
            "status": "success",
            "tool": tool_name,
            "parameters": parameters,
            "result": result,
            "data_quality": "good",
            "validation_notes": [],
        }

        try:
            # 检查是否有错误
            if isinstance(result, dict) and "error" in result:
                validation_info["data_quality"] = "error"
                validation_info["validation_notes"].append(
                    f"工具返回错误: {result['error']}"
                )
                return validation_info

            # 根据工具类型进行特定验证
            if tool_name == "get_historical_data":
                if isinstance(result, dict):
                    if "period_summary" in result:
                        summary = result["period_summary"]
                        if summary.get("total_days", 0) == 0:
                            validation_info["data_quality"] = "poor"
                            validation_info["validation_notes"].append("历史数据为空")
                        elif summary.get("current_price") is None:
                            validation_info["data_quality"] = "poor"
                            validation_info["validation_notes"].append(
                                "缺少当前价格数据"
                            )
                        else:
                            validation_info["validation_notes"].append(
                                f"获取到{summary.get('total_days', 0)}天的历史数据"
                            )

            elif tool_name == "get_financial_statements":
                if isinstance(result, dict) and "key_metrics" in result:
                    metrics = result["key_metrics"]
                    available_metrics = [
                        k for k, v in metrics.items() if v != "N/A" and v is not None
                    ]
                    if len(available_metrics) < 3:
                        validation_info["data_quality"] = "poor"
                        validation_info["validation_notes"].append("财务指标数据不完整")
                    else:
                        validation_info["validation_notes"].append(
                            f"获取到{len(available_metrics)}个有效财务指标"
                        )

            elif tool_name == "get_stock_news":
                if isinstance(result, list):
                    if len(result) == 0:
                        validation_info["data_quality"] = "poor"
                        validation_info["validation_notes"].append("未找到相关新闻")
                    else:
                        validation_info["validation_notes"].append(
                            f"获取到{len(result)}条新闻"
                        )

            elif tool_name == "calculate_technical_indicators":
                if isinstance(result, dict) and "indicators" in result:
                    indicators = result["indicators"]
                    valid_indicators = 0
                    for category, values in indicators.items():
                        if isinstance(values, dict):
                            valid_indicators += len(
                                [v for v in values.values() if v is not None]
                            )
                        elif values is not None:
                            valid_indicators += 1

                    if valid_indicators < 5:
                        validation_info["data_quality"] = "poor"
                        validation_info["validation_notes"].append("技术指标数据不完整")
                    else:
                        validation_info["validation_notes"].append(
                            f"计算出{valid_indicators}个有效技术指标"
                        )

            # 添加数据时效性检查
            from datetime import datetime

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            validation_info["data_timestamp"] = current_time
            validation_info["validation_notes"].append(f"数据获取时间: {current_time}")

            logger.info(
                f"工具{tool_name}数据验证完成，质量: {validation_info['data_quality']}"
            )
            return validation_info

        except Exception as e:
            logger.error(f"数据验证失败: {str(e)}")
            validation_info["data_quality"] = "unknown"
            validation_info["validation_notes"].append(f"验证过程出错: {str(e)}")
            return validation_info

    def analyze(
        self, user_query: str, max_steps: int = 5, step_callback=None
    ) -> Dict[str, Any]:
        """处理用户查询，进行分析"""
        logger.info(f"开始分析用户查询: {user_query}")
        self.conversation_history.append({"role": "user", "content": user_query})

        steps = []
        final_analysis = None
        total_tokens_used = 0

        for step in range(max_steps):
            logger.info(f"执行分析步骤 {step+1}/{max_steps}")
            # 调用大模型获取响应
            logger.debug(f"向OpenAI发送请求，模型: {self.model_name}")
            response = self.openai_client.chat.completions.create(
                model=self.model_name, messages=self.conversation_history
            )

            # 统计token使用量
            step_tokens = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            total_tokens_used += step_tokens["total_tokens"]

            llm_response = response.choices[0].message.content
            logger.info(
                f"OpenAI API调用完成 - 步骤{step+1} Token使用: {step_tokens['prompt_tokens']} prompt + {step_tokens['completion_tokens']} completion = {step_tokens['total_tokens']} total"
            )
            logger.debug(f"收到OpenAI响应: {llm_response}")
            self.conversation_history.append(
                {"role": "assistant", "content": llm_response}
            )

            # 记录步骤
            step_data = {
                "step": step + 1,
                "llm_response": llm_response,
                "token_usage": step_tokens,
            }
            steps.append(step_data)

            # 实时发送思考过程
            if step_callback:
                # 提取不包含工具调用标记的部分
                clean_response = llm_response
                tool_call_start = clean_response.find("<tool_call>")
                if tool_call_start != -1:
                    clean_response = clean_response[:tool_call_start].strip()

                if clean_response.strip():
                    step_callback(
                        {
                            "type": "thinking",
                            "content": f"💭 步骤 {step+1}: {clean_response}",
                        }
                    )

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
                    step_callback(
                        {
                            "type": "tool",
                            "content": f"📊 正在获取 {ticker} 的历史数据...",
                        }
                    )
                elif tool_name == "get_financial_statements":
                    ticker = tool_params.get("ticker", "")
                    step_callback(
                        {
                            "type": "tool",
                            "content": f"📈 正在获取 {ticker} 的财务报表...",
                        }
                    )
                elif tool_name == "get_news":
                    ticker = tool_params.get("ticker", "")
                    step_callback(
                        {
                            "type": "tool",
                            "content": f"📰 正在获取 {ticker} 的最新新闻...",
                        }
                    )
                elif tool_name == "calculate_technical_indicators":
                    ticker = tool_params.get("ticker", "")
                    step_callback(
                        {
                            "type": "tool",
                            "content": f"📉 正在计算 {ticker} 的技术指标...",
                        }
                    )
                else:
                    step_callback(
                        {"type": "tool", "content": f"🔧 正在调用工具: {tool_name}"}
                    )

            tool_result = self._run_tool(tool_call)
            steps[-1]["tool_call"] = tool_call
            steps[-1]["tool_result"] = tool_result

            # 记录工具调用的详细日志
            tool_log_data = {
                "tool_name": tool_call.get("name", "unknown"),
                "tool_parameters": tool_call.get("parameters", {}),
                "tool_execution_status": tool_result.get("status", "unknown"),
                "data_quality": tool_result.get("data_quality", "unknown"),
                "validation_notes": tool_result.get("validation_notes", []),
                "tool_result": tool_result.get("result", {}),
            }
            logger.info(
                f"工具调用详情: {json.dumps(tool_log_data, ensure_ascii=False, indent=2)}"
            )

            # 发送工具执行完成信息
            if step_callback:
                step_callback(
                    {"type": "thinking", "content": "✅ 工具执行完成，正在分析结果..."}
                )

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
            tool_result_msg = (
                f"工具调用结果:\n{json.dumps(serializable_result, indent=2)}"
            )
            logger.debug(f"工具调用结果: {json.dumps(serializable_result)}")
            self.conversation_history.append(
                {"role": "user", "content": tool_result_msg}
            )

        # 如果达到最大步数但还没有最终分析，请求一个总结
        if final_analysis is None:
            logger.info("达到最大步数限制，请求最终分析总结")
            summary_prompt = "请基于以上所有信息，提供一个完整的分析总结和投资建议。不要再调用任何工具。"
            self.conversation_history.append(
                {"role": "user", "content": summary_prompt}
            )

            response = self.openai_client.chat.completions.create(
                model=self.model_name, messages=self.conversation_history
            )

            # 统计最终总结的token使用量
            final_tokens = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            total_tokens_used += final_tokens["total_tokens"]

            final_analysis = response.choices[0].message.content
            logger.info(
                f"最终分析总结完成 - Token使用: {final_tokens['prompt_tokens']} prompt + {final_tokens['completion_tokens']} completion = {final_tokens['total_tokens']} total"
            )

            # 记录最终总结步骤
            steps.append(
                {
                    "step": len(steps) + 1,
                    "llm_response": final_analysis,
                    "token_usage": final_tokens,
                    "is_final_summary": True,
                }
            )

        # 发送最终分析结果
        if step_callback and final_analysis:
            step_callback({"type": "final", "content": final_analysis})

        # 记录总体token使用统计
        logger.info(
            f"分析完成 - 总Token消耗: {total_tokens_used} tokens，共执行{len(steps)}个步骤"
        )

        return {
            "query": user_query,
            "steps": steps,
            "final_analysis": final_analysis,
            "completed": final_analysis is not None,
            "total_tokens_used": total_tokens_used,
            "steps_count": len(steps),
        }
