# 代码交接助手 - Code Handover Agent

一个基于 AI Agent 的代码项目交接助手，采用 Y2K 风格设计的智能交接平台。帮助员工快速理解代码项目，实现高效的知识传递。

## 🎯 核心功能

### 界面一：智能助手聊天
- Y2K 风格设计的对话界面
- GitHub 仓库链接分析与报告生成
- 实时 AI 对话，解答代码相关问题
- 进度可视化（仓库链接 → 分析中 → 完成报告）
- 支持快捷命令：`/reset`、`/skills`、`/tasks`

### 界面二：交接报告展示
- 六大交接模块的可视化展示
  - **项目概述**：项目背景、目标与定位
  - **目录结构**：文件组织架构
  - **入口点**：程序启动流程
  - **核心模块**：关键组件解析
  - **依赖关系**：项目依赖图谱
  - **项目人员**：团队结构与贡献者
- 侧边栏快速导航
- Markdown 内容渲染
- 交接报告下载功能
- 一键返回 AI 助手继续对话

## 💡 使用场景

- 👥 **员工离职交接**：快速将项目知识传递给接手人
- 🆕 **新成员入职**：帮助新员工快速了解代码库
- 🔄 **项目转移**：跨团队项目交接
- 📚 **知识沉淀**：生成项目文档供后续参考

## 🏗️ 技术架构

### 后端
- **Flask** - Web 框架
- **Agent Runner** - 调用本地 AI Agent 进行代码分析
- **CORS** - 跨域请求支持
- **会话保持** - 全局 Agent 实例维持对话上下文

### Agent 后端连接
Dashboard 通过以下方式连接到后端 Agent：

```
dashboard/
├── server.py                    # Flask 服务器
└── (通过 sys.path 连接) →
    └── ../my-mini-cc-main/      # Agent 后端目录
        ├── agent_runner.py       # Agent 调用器
        ├── core/                 # Agent 核心逻辑
        ├── agent/                # Agent 定义
        ├── skills/               # 技能定义（包括 project-code-understanding）
        └── config.py             # 配置文件
```

**连接机制**：
```python
# server.py 中的连接代码
AGENT_PATH = Path(__file__).parent.parent / "my-mini-cc-main"
sys.path.insert(0, str(AGENT_PATH))
from agent_runner import AgentRunner
```

### 前端
- **HTML5 + CSS3** - 响应式布局
- **Tailwind CSS** - 样式框架
- **Lucide Icons** - 图标库
- **Marked.js** - Markdown 解析
- **Y2K 渐变风格** - 复古未来主义设计

## 📁 项目结构

```
dashboard/
├── server.py                         # Flask 后端服务器
├── requirements.txt                  # Python 依赖
├── README.md                         # 项目说明
├── analysis_results/                 # 分析报告存储
└── .superdesign/
    └── design_iterations/
        ├── chat_y2k_v1.html         # 主界面：AI 助手聊天
        └── report.html               # 报告页面：交接文档展示
```

## 🚀 安装和运行

### 前置要求

1. **Python 3.8+**
2. **本地 AI Agent 环境** (位于 `../my-mini-cc-main`)
3. **API 配置** - 需要配置 LLM API (如 Zhipu AI、OpenAI 等)

### 安装步骤

#### 1. 安装 Dashboard 依赖

```bash
cd dashboard
pip install -r requirements.txt
```

Dashboard 依赖包括：
- `flask` - Web 框架
- `flask-cors` - 跨域支持
- `litellm` - LLM 统一接口

#### 2. 配置 Agent 后端

```bash
cd ../my-mini-cc-main
pip install -r requirements.txt
```

Agent 后端依赖包括：
- `litellm` - LLM 调用
- `openai` - OpenAI SDK
- `zhipuai` - 智谱 AI SDK
- 其他工具库

#### 3. 配置 API 密钥

Agent 需要配置 LLM API 密钥才能工作。编辑 Agent 的配置文件：

```bash
cd ../my-mini-cc-main
```

编辑 `config.py` 或设置环境变量：

**方式一：环境变量（推荐）**
```bash
# Windows (PowerShell)
$env:ZHIPUAI_API_KEY="your_api_key_here"
$env:LITELLM_MODEL="zhipu/glm-4.7"

# Linux/Mac
export ZHIPUAI_API_KEY="your_api_key_here"
export LITELLM_MODEL="zhipu/glm-4.7"
```

**方式二：修改配置文件**

在 `my-mini-cc-main/config.py` 中设置：

```python
class Settings:
    # API 配置
    api_key = "your_api_key_here"
    model = "zhipu/glm-4.7"  # 或 "gpt-4" 等

    # 其他配置...
    workdir = Path.cwd()
```

#### 4. 验证 Agent 连接

运行以下命令验证 Agent 是否正常工作：

```bash
cd ../my-mini-cc-main
python -c "from agent_runner import AgentRunner; print('Agent 加载成功！')"
```

如果输出了 "Agent 加载成功！"，说明配置正确。

### 启动服务器

```bash
cd dashboard
python server.py
```

**启动输出示例**：
```
============================================================
  AI Agent 分析工具 - 后端服务器
============================================================
服务器地址: http://localhost:5000
Agent 路径: D:\code\aiagent\my-mini-cc-main
结果存储: D:\code\aiagent\dashboard\analysis_results
============================================================
 * Serving Flask app 'server'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

服务器将在 `http://localhost:5000` 启动。

**Windows 快捷启动**（可选）：
```bash
cd dashboard
.\start.bat
```

### 访问应用

打开浏览器访问：`http://localhost:5000`

## 📖 使用指南

### 方式一：生成交接报告

1. **输入 GitHub 仓库链接**
   - 在首页输入框粘贴仓库地址
   - 格式：`https://github.com/owner/repo`

2. **点击「分析」按钮**
   - 系统调用 AI 分析代码库
   - 显示实时进度状态

3. **查看交接报告**
   - 分析完成后自动跳转到报告页
   - 浏览各个交接模块
   - 下载完整交接文档

### 方式二：与 AI 助手对话

1. **直接提问**
   - 在聊天界面输入关于代码的问题
   - AI 助手会基于项目上下文回答

2. **快捷命令**
   - `/reset` - 重置对话历史
   - `/skills` - 查看 AI 可用技能
   - `/tasks` - 查看当前任务状态

### 方式三：报告 + 对话组合

1. 先生成交接报告了解项目概况
2. 点击「继续对话」返回 AI 助手
3. 针对具体问题深入讨论
4. 随时可以返回查看报告细节

## 🔌 Agent Runner 接口

Dashboard 通过 `AgentRunner` 类调用后端 Agent：

### 核心方法

```python
from agent_runner import AgentRunner
from pathlib import Path

# 创建 AgentRunner 实例
runner = AgentRunner(workdir=Path("../my-mini-cc-main"))

# 方法1: 分析 GitHub 仓库
report = runner.analyze_repository("https://github.com/owner/repo")

# 方法2: 分析本地项目路径
report = runner.analyze_local_path("D:\\code\\my_project")

# 方法3: 通用聊天接口（自动检测 GitHub URL）
response = runner.chat("请解释这个项目的核心模块")

# 方法4: 重置对话上下文
runner.reset()
```

### 内部工作流程

```
用户请求
    ↓
server.py (Flask API)
    ↓
AgentRunner.analyze_repository() / chat()
    ↓
MiniCC Agent (核心逻辑)
    ↓
project-code-understanding Skill
    ↓
LLM API (Zhipu AI / OpenAI / ...)
    ↓
分析结果 (Markdown 格式)
    ↓
解析并返回给前端
```

## 🔌 API 接口

### POST /api/analyze
分析 GitHub 仓库并生成交接报告

**请求体：**
```json
{
  "url": "https://github.com/owner/repo"
}
```

**响应：**
```json
{
  "success": true,
  "analysis_id": "owner_repo_20250322_123456",
  "message": "分析完成",
  "redirect_url": "/report/owner_repo_20250322_123456"
}
```

### POST /api/chat
与 AI 助手进行对话

**请求体：**
```json
{
  "message": "这个项目的主要功能是什么？",
  "analysis_id": "owner_repo_20250322_123456"
}
```

**响应：**
```json
{
  "success": true,
  "response": "该项目的主要功能是..."
}
```

### GET /api/report/<analysis_id>
获取交接报告内容

**响应：**
```json
{
  "success": true,
  "sections": {
    "overview": "项目概述内容...",
    "directory": "目录结构内容...",
    "entrypoints": "入口点内容...",
    "modules": "核心模块内容...",
    "dependencies": "依赖关系内容...",
    "team": "项目人员内容..."
  }
}
```

### GET /api/download/<analysis_id>
下载交接报告（Markdown 文件）

## ⚙️ 配置选项

### 服务器配置

在 `server.py` 中可以修改以下配置：

```python
# 服务器端口
app.run(debug=True, host='0.0.0.0', port=5000)

# Agent 路径
AGENT_PATH = Path(__file__).parent.parent / "my-mini-cc-main"

# 结果存储目录
RESULTS_DIR = Path(__file__).parent / "analysis_results"
```

## 🎨 设计风格

项目采用 Y2K（千禧年）复古未来主义设计风格：

- **色彩**：紫粉渐变系（powder-petal → mauve → wisteria → soft-periwinkle）
- **背景**：深紫色调 + 动态渐变 + 星星装饰
- **元素**：玻璃态、圆角、发光效果
- **动画**：渐变移动、闪烁、浮动

## 🛠️ 开发说明

### 添加新的交接模块

1. 在 Agent skill 中添加新的分析模块
2. 在 `parse_markdown_sections` 函数中添加对应的解析逻辑
3. 在报告页面 HTML 中添加新的导航项和内容区域

### 自定义样式

Y2K 风格的 CSS 变量定义在 HTML 文件的 `<style>` 标签中：

```css
:root {
    --powder-petal: #efd9ce;
    --mauve: #dec0f1;
    --wisteria: #b79ced;
    --soft-periwinkle: #957fef;
    --medium-slate-blue: #7170ef;
    /* ... 更多变量 */
}
```

## 🔧 故障排除

### Agent 导入失败

**错误**：`ModuleNotFoundError: No module named 'agent_runner'`

**解决方案**：
1. 确认 Agent 目录路径正确
   ```python
   # 在 server.py 中检查
   AGENT_PATH = Path(__file__).parent.parent / "my-mini-cc-main"
   print(f"Agent path: {AGENT_PATH}, exists: {AGENT_PATH.exists()}")
   ```

2. 确认 Agent 依赖已安装
   ```bash
   cd ../my-mini-cc-main
   pip install -r requirements.txt
   ```

3. 确认 Agent 目录结构完整
   ```
   my-mini-cc-main/
   ├── agent_runner.py
   ├── core/
   ├── agent/
   └── skills/
   ```

### API 调用失败

**错误**：`API key not configured` 或 `Authentication failed`

**解决方案**：
1. 检查 API 密钥是否已配置
   ```bash
   # Windows
   echo $env:ZHIPUAI_API_KEY

   # Linux/Mac
   echo $ZHIPUAI_API_KEY
   ```

2. 检查 Agent 配置文件中的 API 设置
   ```bash
   cd ../my-mini-cc-main
   cat config.py | grep -i api
   ```

3. 确认 API 密钥有效且有足够额度

### Agent 调用超时

**错误**：分析请求长时间无响应

**解决方案**：
1. 检查网络连接是否正常
2. 尝试使用较小的测试项目
3. 在 Agent 配置中增加超时时间
4. 查看 Agent 日志了解详细情况

### 报告生成失败

**错误**：分析完成后报告页面显示异常

**解决方案**：
1. 确认分析任务已完成
   ```bash
   ls dashboard/analysis_results/
   ```

2. 检查生成的 Markdown 文件格式
   ```bash
   cat dashboard/analysis_results/<analysis_id>.md
   ```

3. 如果 AI 未按格式输出，这是模型限制。可以：
   - 尝试不同的 LLM 模型
   - 分析较小的项目
   - 在非高峰时段重试

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题，请联系项目维护者。
