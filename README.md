# 股票分析系统

一个基于大语言模型的智能股票分析系统，提供交互式Web界面，支持自然语言查询和数据可视化。

## 功能特点

- **自然语言查询**：使用自然语言提问关于股票的各种问题
- **实时思考过程**：展示AI分析股票数据的思考过程
- **数据可视化**：自动生成股票价格和技术指标图表
- **技术分析**：支持移动平均线、RSI、MACD等技术指标分析
- **基本面分析**：获取公司财务报表和关键指标
- **新闻分析**：整合相关股票新闻

## 技术栈

- **后端**：Python、Flask、OpenAI API
- **前端**：HTML、CSS、JavaScript、Chart.js
- **数据源**：YFinance、Alpha Vantage、News API

## 安装步骤

1. 克隆仓库

```bash
git clone https://github.com/yourusername/stock-agent.git
cd stock-agent
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

- 股票价格分析
- 技术指标计算
- 公司财务状况
- 相关新闻整合
- 投资建议生成

## 项目结构

```
├── app.py              # Flask应用入口
├── llm_agent.py        # 大语言模型代理
├── tools.py            # 工具类定义
├── logger.py           # 日志配置
├── static/             # 静态资源
│   ├── css/            # 样式文件
│   └── js/             # JavaScript文件
└── templates/          # HTML模板
```

## 环境变量

项目需要以下环境变量：

- `OPENAI_API_KEY`：OpenAI API密钥
- `NEWS_API_KEY`：News API密钥（可选）
- `ALPHA_VANTAGE_API_KEY`：Alpha Vantage API密钥（可选）

## 许可证

MIT