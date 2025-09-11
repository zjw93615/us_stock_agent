import os
from typing import TypedDict, List, Dict, Optional
from langchain.chat_models import ChatOpenAI
from langchain.tools import Tool
from langchain.utilities import SerpAPIWrapper
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langgraph.graph import StateGraph, END

# 设置API密钥（实际使用时建议通过环境变量加载）
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
os.environ["SERPAPI_API_KEY"] = "your-serpapi-api-key"

# 1. 定义状态结构：存储流程中的所有中间数据
class AgentState(TypedDict):
    """定义Agent的状态结构，包含所有需要传递的信息"""
    question: str  # 用户原始问题
    tasks: List[str]  # 拆分后的子任务列表
    intermediate_results: List[Dict]  # 任务执行结果
    evaluation: str  # 信息评估结果
    final_answer: Optional[str]  # 最终回答
    iteration_count: int  # 迭代次数（防止无限循环）
    max_iterations: int  # 最大迭代次数

# 2. 初始化工具和模型
class AgentComponents:
    def __init__(self):
        # 网络搜索工具
        self.search = SerpAPIWrapper()
        self.tools = [
            Tool(
                name="Search",
                func=self.search.run,
                description="用于获取最新信息或需要实时数据的问题，如新闻、统计数据等"
            )
        ]
        
        # 初始化LLM
        self.llm = ChatOpenAI(model_name="gpt-4", temperature=0.7)
        
        # 任务拆分链
        self.task_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["question"],
                template="""将用户问题拆分为需要通过网络搜索完成的子任务，每个任务需具体明确。
用户问题: {question}
输出格式: 以列表形式返回，每个任务单独一行（无需编号）。
"""
            )
        )
        
        # 信息评估链
        self.evaluation_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["question", "results"],
                template="""评估现有搜索结果是否足够回答用户问题。
用户问题: {question}
搜索结果: {results}
评估标准: 1. 是否覆盖问题核心；2. 信息是否全面；3. 是否有时效性（如需要）；4. 是否存在矛盾。
输出要求: 若足够，回答"足够"；若不足，回答"不足够: [需要补充的内容]"。
"""
            )
        )
        
        # 结果总结链
        self.summarization_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                input_variables=["question", "results"],
                template="""基于搜索结果，全面回答用户问题。
用户问题: {question}
搜索结果: {results}
回答需包含：核心结论、支持证据、必要背景，结构清晰。
"""
            )
        )

# 3. 定义节点函数：每个节点处理特定任务并更新状态
class AgentNodes:
    def __init__(self, components: AgentComponents):
        self.components = components
        
    def split_tasks(self, state: AgentState) -> AgentState:
        """拆分任务节点：将用户问题拆分为子任务"""
        print(f"=== 拆分任务 ===")
        question = state["question"]
        # 调用任务拆分链
        tasks_str = self.components.task_chain.run(question)
        # 解析任务列表
        tasks = [t.strip() for t in tasks_str.split("\n") if t.strip()]
        print(f"拆分出{len(tasks)}个子任务: {tasks}")
        return {**state, "tasks": tasks}
    
    def execute_tasks(self, state: AgentState) -> AgentState:
        """执行任务节点：处理所有子任务（调用搜索工具）"""
        print(f"\n=== 执行任务 ===")
        tasks = state["tasks"]
        intermediate_results = state["intermediate_results"]
        
        # 执行未完成的任务（首次执行所有任务，补充搜索时只执行新任务）
        for task in tasks:
            # 检查是否已执行过该任务
            if not any(res["task"] == task for res in intermediate_results):
                print(f"执行任务: {task}")
                # 调用搜索工具
                result = self.components.search.run(task)
                intermediate_results.append({
                    "task": task,
                    "result": result
                })
                print(f"任务结果: {result[:100]}...")  # 简化显示
        
        return {** state, "intermediate_results": intermediate_results}
    
    def evaluate_information(self, state: AgentState) -> AgentState:
        """评估节点：判断现有信息是否足够"""
        print(f"\n=== 评估信息 ===")
        question = state["question"]
        results = state["intermediate_results"]
        
        # 格式化搜索结果为字符串
        results_str = "\n".join([f"任务: {r['task']}\n结果: {r['result']}" for r in results])
        # 调用评估链
        evaluation = self.components.evaluation_chain.run(
            question=question,
            results=results_str
        )
        print(f"评估结果: {evaluation}")
        return {**state, "evaluation": evaluation, "iteration_count": state["iteration_count"] + 1}
    
    def generate_summary(self, state: AgentState) -> AgentState:
        """总结节点：基于搜索结果生成最终回答"""
        print(f"\n=== 生成总结 ===")
        question = state["question"]
        results = state["intermediate_results"]
        
        results_str = "\n".join([f"任务: {r['task']}\n结果: {r['result']}" for r in results])
        final_answer = self.components.summarization_chain.run(
            question=question,
            results=results_str
        )
        return {** state, "final_answer": final_answer}
    
    def generate_new_tasks(self, state: AgentState) -> AgentState:
        """生成新任务节点：当信息不足时，生成补充搜索任务"""
        print(f"\n=== 生成补充任务 ===")
        evaluation = state["evaluation"]
        # 从评估结果中提取需要补充的内容
       补充内容 = evaluation.replace("不足够: ", "").strip()
        # 生成新任务（这里简化处理，直接将补充内容作为新任务）
        new_tasks = [补充内容]
        print(f"补充任务: {new_tasks}")
        return {**state, "tasks": new_tasks}

# 4. 定义边的逻辑：控制流程走向
def should_continue(state: AgentState) -> str:
    """判断流程是否继续搜索或进入总结"""
    evaluation = state["evaluation"]
    iteration_count = state["iteration_count"]
    max_iterations = state["max_iterations"]
    
    # 如果信息足够或达到最大迭代次数，进入总结
    if "足够" in evaluation or iteration_count >= max_iterations:
        return "to_summary"
    # 否则继续补充搜索
    return "to_new_tasks"

# 5. 构建LangGraph图
def build_agent_graph(max_iterations: int = 3) -> StateGraph:
    # 初始化组件和节点
    components = AgentComponents()
    nodes = AgentNodes(components)
    
    # 创建状态图
    graph = StateGraph(AgentState)
    
    # 添加节点
    graph.add_node("split_tasks", nodes.split_tasks)  # 拆分任务
    graph.add_node("execute_tasks", nodes.execute_tasks)  # 执行任务
    graph.add_node("evaluate_information", nodes.evaluate_information)  # 评估信息
    graph.add_node("generate_new_tasks", nodes.generate_new_tasks)  # 生成新任务
    graph.add_node("generate_summary", nodes.generate_summary)  # 生成总结
    
    # 定义边：流程走向
    graph.set_entry_point("split_tasks")  # 入口节点
    graph.add_edge("split_tasks", "execute_tasks")  # 拆分任务后执行任务
    graph.add_edge("execute_tasks", "evaluate_information")  # 执行后评估
    graph.add_conditional_edges(  # 评估后根据条件分支
        "evaluate_information",
        should_continue,
        {
            "to_new_tasks": "generate_new_tasks",  # 信息不足→生成新任务
            "to_summary": "generate_summary"  # 信息足够→生成总结
        }
    )
    graph.add_edge("generate_new_tasks", "execute_tasks")  # 新任务→执行
    graph.add_edge("generate_summary", END)  # 总结后结束
    
    # 编译图
    return graph.compile()

# 6. 使用示例
if __name__ == "__main__":
    # 构建图
    agent_graph = build_agent_graph(max_iterations=3)
    
    # 定义初始状态
    user_question = "2024年全球人工智能领域的主要突破有哪些？这些突破对医疗行业会产生什么具体影响？"
    initial_state = {
        "question": user_question,
        "tasks": [],
        "intermediate_results": [],
        "evaluation": "",
        "final_answer": None,
        "iteration_count": 0,
        "max_iterations": 3
    }
    
    # 运行图
    print(f"处理问题: {user_question}\n")
    result = agent_graph.invoke(initial_state)
    
    # 输出结果
    print("\n\n==================== 最终回答 ====================")
    print(result["final_answer"])
    