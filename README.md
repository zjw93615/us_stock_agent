# 股票分析系统

一个基于大语言模型的智能股票分析系统，提供交互式Web界面，支持自然语言查询、实时数据分析和数学公式渲染。

## 功能特点

- **自然语言查询**：使用自然语言提问关于股票的各种问题
- **实时思考过程**：展示AI分析股票数据的思考过程和推理链
- **数据可视化**：自动生成股票价格和技术指标图表
- **技术分析**：支持移动平均线、RSI、MACD、布林带、KDJ等多种技术指标
- **基本面分析**：获取公司财务报表、市值、PE比率等关键指标
- **新闻分析**：整合相关股票新闻和市场信息
- **网络搜索**：集成SerpAPI进行实时信息搜索
- **数学公式渲染**：支持MathJax渲染复杂的金融公式
- **模块化工具架构**：可扩展的工具系统，支持自定义分析工具

## 技术栈

- **后端**：Python、Flask、OpenAI API、LangChain
- **前端**：HTML、CSS、JavaScript、Chart.js、MathJax
- **数据源**：YFinance、GNews、SerpAPI
- **AI模型**：支持OpenAI GPT系列、Qwen等多种大语言模型

## 安装步骤

1. 克隆仓库

```bash
git clone https://github.com/zjw93615/us_stock_agent.git
cd us_stock_agent
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

复制`.env.template`文件为`.env`并填入必要的API密钥：

```bash
cp .env.template .env
# 编辑.env文件，填入API密钥
```

## 使用方法

1. 启动应用

```bash
python app.py
```

2. 在浏览器中访问 http://127.0.0.1:5000

3. 在输入框中输入自然语言查询，例如：
   - "分析特斯拉股票最近一个月的表现"
   - "比较苹果和微软的市盈率"
   - "计算亚马逊股票的RSI指标"
   - "获取谷歌最近的财务报表"

## 快速查询示例

### 基础查询
- "分析特斯拉股票最近一个月的表现"
- "比较苹果和微软的市盈率"
- "计算亚马逊股票的RSI指标"
- "获取谷歌最近的财务报表"
- "搜索关于英伟达最新的市场新闻"

### 高级分析
- "使用DCF模型计算苹果公司的企业价值"
- "分析特斯拉的技术指标并给出投资建议"
- "比较科技股的估值水平"
- "分析市场趋势和宏观经济影响"

### 数学公式支持
系统支持渲染复杂的金融公式，如：
- 企业价值计算：$$ \text{企业价值} = \sum_{t=1}^{n} \frac{FCF_t}{(1 + WACC)^t} + \frac{TV}{(1 + WACC)^n} $$
- 终值计算：$$ TV = \frac{FCF_{n+1}}{WACC - g} $$
- 技术指标公式等

## 项目结构

```
├── app.py                      # Flask应用入口
├── llm_agent.py               # 大语言模型代理
├── tool_manager.py            # 工具管理器
├── logger.py                  # 日志配置
├── web_search_tool.py         # 网络搜索工具（独立文件）
├── static/                    # 静态资源
│   ├── css/
│   │   └── style.css         # 主样式文件
│   └── js/
│       └── main.js           # 前端交互逻辑
├── templates/
│   └── index.html            # 主页模板
├── tools/                     # 工具模块目录
│   ├── __init__.py
│   ├── base_tool.py          # 工具基类
│   ├── historical_data_tool.py      # 历史数据工具
│   ├── financial_statements_tool.py # 财务报表工具
│   ├── news_tool.py          # 新闻获取工具
│   ├── technical_analysis_tool.py   # 技术分析工具
│   ├── stock_info_tool.py    # 股票基本信息工具
│   ├── historical_pe_eps_tool.py    # 历史PE/EPS工具
│   └── web_search_tool.py    # 网络搜索工具
├── temp_ref/                  # 临时参考文件
├── .env.template             # 环境变量模板
├── .env                      # 环境变量配置（需自行创建）
├── requirements.txt          # Python依赖包
└── README.md                 # 项目说明文档
```

## 环境变量

项目需要以下环境变量（参考`.env.template`文件）：

### 必需配置
- `OPENAI_API_KEY`：OpenAI API密钥
- `SERPAPI_API_KEY`：SerpAPI密钥（用于网络搜索功能）

### 可选配置
- `OPENAI_MODEL`：使用的AI模型（默认：qwen-flash）
- `NEWS_API_KEY`：News API密钥（新闻功能，可选）
- `FLASK_ENV`：Flask环境（development/production）
- `FLASK_DEBUG`：调试模式（True/False）
- `FLASK_PORT`：应用端口（默认：5000）
- `LOG_LEVEL`：日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- `HTTP_PROXY`：HTTP代理设置
- `HTTPS_PROXY`：HTTPS代理设置

## 工具架构

系统采用模块化的工具架构，每个工具都继承自`Tool`基类：

### 现有工具
1. **HistoricalDataTool** - 获取股票历史价格数据
2. **FinancialStatementsTool** - 获取公司财务报表
3. **NewsTool** - 获取相关新闻信息
4. **TechnicalAnalysisTool** - 计算技术指标
5. **StockInfoTool** - 获取股票基本信息
6. **WebSearchIntegrationTool** - 网络搜索功能
7. **HistoricalPEEPSTool** - 历史PE/EPS分析

### 添加新工具
1. 在`tools/`目录下创建新的工具文件
2. 继承`Tool`基类并实现`run`方法
3. 在`tool_manager.py`中注册新工具
4. 在`llm_agent.py`中添加工具展示逻辑

## 开发指南

### 前端开发
- 主要逻辑在`static/js/main.js`中
- 支持实时流式响应显示
- 集成MathJax进行数学公式渲染
- 使用Chart.js进行数据可视化

### 后端开发
- Flask应用入口：`app.py`
- AI代理逻辑：`llm_agent.py`
- 工具管理：`tool_manager.py`
- 日志配置：`logger.py`

## 许可证

MIT


## TODO:
创建一个微信小程序，功能和现在的前端功能一样，同时后端也要更新相应的功能
1. 使用自然语言提问关于股票的各种问题，使用流式传输让大模型边输出边展示
2. 添加小程序登陆功能，用户需要登陆才能进行提问
3. 添加小程序广告，没询问一次就必须看一次广告，只有收到成功看完广告了才能进行后端的大模型处理