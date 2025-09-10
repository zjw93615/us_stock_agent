// 全局变量
let isProcessing = false;
let chartInstance = null;

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化表单提交事件
    document.getElementById('query-form').addEventListener('submit', handleSubmit);
});

/**
 * 处理表单提交
 */
async function handleSubmit(event) {
    event.preventDefault();
    
    // 如果正在处理请求，则忽略
    if (isProcessing) return;
    
    const queryInput = document.getElementById('query-input');
    const query = queryInput.value.trim();
    
    if (!query) return;
    
    // 显示用户消息
    addMessage('user', query);
    
    // 清空输入框
    queryInput.value = '';
    
    // 显示加载动画
    showLoading();
    
    // 设置处理标志
    isProcessing = true;
    
    // 创建思考过程容器
    const thinkingId = 'thinking-' + Date.now();
    const chatMessages = document.getElementById('chat-messages');
    const thinkingDiv = document.createElement('div');
    thinkingDiv.id = thinkingId;
    thinkingDiv.className = 'message system-message thinking-message';
    
    const thinkingHeader = document.createElement('div');
    thinkingHeader.className = 'thinking-header';
    thinkingHeader.textContent = '思考过程：';
    
    const thinkingSteps = document.createElement('div');
    thinkingSteps.className = 'thinking-steps';
    
    thinkingDiv.appendChild(thinkingHeader);
    thinkingDiv.appendChild(thinkingSteps);
    chatMessages.appendChild(thinkingDiv);
    
    try {
        // 使用流式API获取实时思考过程
        const response = await fetch('/api/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });
        
        if (!response.ok) {
            throw new Error('请求失败');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let finalResponse = null;
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            const text = decoder.decode(value, { stream: true });
            const lines = text.split('\n').filter(line => line.trim() !== '');
            
            for (const line of lines) {
                try {
                    const data = JSON.parse(line);
                    
                    if (data.type === 'thinking') {
                        // 添加思考步骤
                        const stepDiv = document.createElement('div');
                        stepDiv.className = 'thinking-step';
                        stepDiv.innerHTML = marked.parse(data.content);
                        thinkingSteps.appendChild(stepDiv);
                        
                        // 滚动到底部
                        scrollToBottom();
                    } else if (data.type === 'tool') {
                        // 添加工具调用信息
                        const toolDiv = document.createElement('div');
                        toolDiv.className = 'thinking-tool';
                        toolDiv.innerHTML = marked.parse(data.content);
                        thinkingSteps.appendChild(toolDiv);
                        
                        // 滚动到底部
                        scrollToBottom();
                    } else if (data.type === 'final') {
                        // 保存最终分析结果
                        finalResponse = data.content;
                    } else if (data.type === 'error') {
                        // 处理错误信息
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'thinking-error';
                        errorDiv.innerHTML = `❌ ${marked.parse(data.content)}`;
                        thinkingSteps.appendChild(errorDiv);
                        
                        // 滚动到底部
                        scrollToBottom();
                    }
                } catch (e) {
                    console.error('解析流数据出错:', e);
                }
            }
        }
        
        // 移除加载动画
        removeLoading();
        
        // 显示最终分析结果
        if (finalResponse) {
            addMessage('assistant', finalResponse);
        } else {
            addMessage('system', '分析完成，但未能获取到最终结果。');
        }
        
        // 保持思考过程显示，但添加完成标记
        const thinkingContainer = document.getElementById(thinkingId);
        if (thinkingContainer) {
            const completedMark = document.createElement('div');
            completedMark.className = 'thinking-completed';
            completedMark.innerHTML = '✅ 思考过程完成';
            thinkingContainer.appendChild(completedMark);
        }
        
        // 发送请求获取可视化数据
        // const visualResponse = await fetch('/api/visualization', {
        //     method: 'POST',
        //     headers: {
        //         'Content-Type': 'application/json'
        //     },
        //     body: JSON.stringify({ query })
        // });
        
        // if (visualResponse.ok) {
        //     const visualData = await visualResponse.json();
        //     if (visualData && visualData.data) {
        //         showVisualization(visualData.ticker || '', visualData);
        //     }
        // }
        
    } catch (error) {
        console.error('分析请求失败:', error);
        removeLoading();
        addMessage('system', '很抱歉，分析过程中出现错误。请稍后再试。');
    } finally {
        // 重置处理标志
        isProcessing = false;
    }
}

/**
 * 添加消息到聊天区域
 */
function addMessage(type, content, thinkingProcess = null) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    
    // 设置消息类型样式
    messageDiv.className = `message ${type}-message`;
    
    // 创建消息内容容器
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // 创建头像容器
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    
    // 根据消息类型设置不同的图标
    if (type === 'user') {
        avatarDiv.innerHTML = '<i class="fas fa-user"></i>';
    } else if (type === 'assistant') {
        avatarDiv.innerHTML = '<i class="fas fa-robot"></i>';
    } else {
        avatarDiv.innerHTML = '<i class="fas fa-info-circle"></i>';
    }
    
    // 将头像添加到消息div
    messageDiv.appendChild(avatarDiv);
    
    // 使用marked.js渲染Markdown内容
    contentDiv.innerHTML = marked.parse(content);
    
    // 添加思考过程（如果有）
    if (thinkingProcess) {
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'thinking-process';
        thinkingDiv.innerHTML = marked.parse(thinkingProcess);
        contentDiv.appendChild(thinkingDiv);
    }
    
    // 将内容添加到消息div
    messageDiv.appendChild(contentDiv);
    
    // 添加到聊天区域
    chatMessages.appendChild(messageDiv);
    
    // 使用MathJax渲染数学公式
    if (window.MathJax && window.MathJax.startup && window.MathJax.startup.document) {
        // 确保MathJax已完全初始化
        MathJax.startup.promise.then(() => {
            return MathJax.typesetPromise([messageDiv]);
        }).then(() => {
            // 数学公式渲染完成后滚动到底部
            scrollToBottom();
        }).catch((err) => {
            console.log('MathJax渲染错误:', err);
            scrollToBottom();
        });
    } else if (window.MathJax) {
        // 如果MathJax存在但未完全初始化，等待一段时间后重试
        setTimeout(() => {
            if (window.MathJax.typesetPromise) {
                MathJax.typesetPromise([messageDiv]).then(() => {
                    scrollToBottom();
                }).catch((err) => {
                    console.log('MathJax渲染错误:', err);
                    scrollToBottom();
                });
            } else {
                scrollToBottom();
            }
        }, 100);
    } else {
        // 如果MathJax未加载，直接滚动到底部
        scrollToBottom();
    }
}

/**
 * 滚动到底部
 */
function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * 显示加载动画
 */
function showLoading() {
    const chatMessages = document.getElementById('chat-messages');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.id = 'loading-indicator';
    
    const dotsDiv = document.createElement('div');
    dotsDiv.className = 'loading-dots';
    
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('span');
        dotsDiv.appendChild(dot);
    }
    
    loadingDiv.appendChild(dotsDiv);
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * 移除加载动画
 */
function removeLoading() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

/**
 * 处理分析步骤
 */
function processAnalysisSteps(steps) {
    if (!steps || !steps.length) return;
    
    // 添加思考过程
    const thinkingSteps = steps.map(step => {
        let stepContent = `**步骤 ${step.step}**: `;
        
        // 添加LLM思考
        if (step.llm_response) {
            // 提取不包含工具调用标记的部分
            let cleanResponse = step.llm_response;
            const toolCallStart = cleanResponse.indexOf('<tool_call>');
            if (toolCallStart !== -1) {
                cleanResponse = cleanResponse.substring(0, toolCallStart).trim();
            }
            
            stepContent += cleanResponse;
        }
        
        // 添加工具调用信息
        if (step.tool_call) {
            stepContent += `\n\n*调用工具: ${step.tool_call.name}*`;
        }
        
        return stepContent;
    }).join('\n\n');
    
    // 添加系统消息，显示思考过程
    addMessage('system', '分析过程:', thinkingSteps);
}

/**
 * 检查是否有可视化数据
 */
function checkForVisualizationData(result) {
    // 在实际实现中，这里会解析结果中的数据，查找可视化的机会
    // 目前仅作为示例，检查是否有历史数据或技术指标
    let hasVisualizationData = false;
    let ticker = '';
    
    // 遍历步骤，查找工具调用结果
    if (result.steps) {
        for (const step of result.steps) {
            if (step.tool_result && step.tool_call) {
                // 检查是否是历史数据或技术指标工具
                const toolName = step.tool_call.name;
                if (
                    toolName === 'get_historical_data' || 
                    toolName === 'calculate_technical_indicators'
                ) {
                    hasVisualizationData = true;
                    // 尝试获取股票代码
                    if (step.tool_call.parameters && step.tool_call.parameters.ticker) {
                        ticker = step.tool_call.parameters.ticker;
                    }
                    break;
                }
            }
        }
    }
    
    // 如果有可视化数据，显示可视化区域
    if (hasVisualizationData && ticker) {
        showVisualization(ticker, result);
    }
}

/**
 * 显示可视化区域
 */
function showVisualization(ticker, data) {
    const visualizationArea = document.getElementById('visualization-area');
    visualizationArea.classList.remove('d-none');
    
    // 显示加载消息
    const chartContainer = document.getElementById('chart-container');
    chartContainer.innerHTML = `<div class="alert alert-info">正在准备 ${ticker} 的数据可视化...</div>`;
    
    // 滚动到可视化区域
    visualizationArea.scrollIntoView({ behavior: 'smooth' });
    
    // 获取可视化数据
    fetchVisualizationData(ticker, data);
}

/**
 * 获取可视化数据并绘制图表
 */
async function fetchVisualizationData(ticker, analysisData) {
    try {
        // 从分析数据中提取日期范围
        let startDate = '';
        let endDate = '';
        let chartType = 'price'; // 默认显示价格图表
        
        // 尝试从分析步骤中提取日期范围和图表类型
        if (analysisData.steps) {
            for (const step of analysisData.steps) {
                if (step.tool_call && step.tool_call.parameters) {
                    const params = step.tool_call.parameters;
                    
                    if (params.start_date) startDate = params.start_date;
                    if (params.end_date) endDate = params.end_date;
                    
                    // 根据工具类型决定图表类型
                    if (step.tool_call.name === 'calculate_technical_indicators') {
                        chartType = 'technical';
                        break;
                    }
                }
            }
        }
        
        // 发送请求获取可视化数据
        const response = await fetch('/api/visualization', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ticker,
                start_date: startDate,
                end_date: endDate,
                chart_type: chartType
            })
        });
        
        if (!response.ok) {
            throw new Error('获取可视化数据失败');
        }
        
        const visualData = await response.json();
        
        if (visualData.status === 'success') {
            // 绘制图表
            drawChart(visualData);
        } else {
            throw new Error(visualData.message || '获取可视化数据失败');
        }
    } catch (error) {
        console.error('可视化数据获取失败:', error);
        const chartContainer = document.getElementById('chart-container');
        chartContainer.innerHTML = `<div class="alert alert-danger">无法生成 ${ticker} 的数据可视化: ${error.message}</div>`;
    }
}

/**
 * 绘制图表
 */
function drawChart(visualData) {
    // 清除现有图表
    if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
    }
    
    const chartContainer = document.getElementById('chart-container');
    chartContainer.innerHTML = '';
    
    // 创建画布
    const canvas = document.createElement('canvas');
    canvas.id = 'chart';
    chartContainer.appendChild(canvas);
    
    // 添加标题
    const titleDiv = document.createElement('div');
    titleDiv.className = 'text-center mt-2 mb-4';
    titleDiv.innerHTML = `<h5>${visualData.title}</h5>`;
    chartContainer.insertBefore(titleDiv, canvas);
    
    // 配置图表选项
    const options = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index',
            intersect: false,
        },
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                usePointStyle: true
            }
        }
    };
    
    // 根据图表类型添加特定配置
    if (visualData.chart_type === 'mixed') {
        // 混合图表（价格+成交量）需要双Y轴
        options.scales = {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                    display: true,
                    text: '价格'
                }
            },
            volume: {
                type: 'linear',
                display: true,
                position: 'right',
                grid: {
                    drawOnChartArea: false
                },
                title: {
                    display: true,
                    text: '成交量'
                }
            }
        };
    } else if (visualData.chart_type === 'line') {
        // 技术指标图表
        options.scales = {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                    display: true,
                    text: '值'
                }
            }
        };
    }
    
    // 创建图表
    const ctx = canvas.getContext('2d');
    chartInstance = new Chart(ctx, {
        type: visualData.chart_type === 'mixed' ? 'line' : visualData.chart_type,
        data: visualData.data,
        options: options
    });
}

/**
 * 隐藏可视化区域
 */
function hideVisualization() {
    const visualizationArea = document.getElementById('visualization-area');
    visualizationArea.classList.add('d-none');
    
    // 清除图表实例
    if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
    }
}

/**
 * 设置查询输入
 */
function setQuery(query) {
    const queryInput = document.getElementById('query-input');
    queryInput.value = query;
    queryInput.focus();
}